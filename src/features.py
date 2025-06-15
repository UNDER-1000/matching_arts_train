from src.classifiers_api import ClassifiersApi
from src.colors_api import ColorsApi
from src.embeddings_api import EmbeddingsApi
import numpy as np
import json
import polars as pl
from src.config import Config
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, not_
from models_db import ArtworkDB
from models import Artwork
from db import engine

class Features:
    def __init__(self, real_api=False):
        self.real_api = real_api
        self.embeddings_api = EmbeddingsApi()
        self.classifier_api = ClassifiersApi()
        self.colors_api = ColorsApi()

        if real_api:
            self.engine = engine
            self.AsyncSessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self.csv_name = Config.csv_name
            self.artwork_id = self.read_images_ids()
            if Config.restart:
                colors_df = self.colors_api.pp(artwork_id=self.artwork_id)
                embeddings_df = self.embeddings_api.pp(artwork_id=self.artwork_id)
                embeddings = np.array([json.loads(e) for e in embeddings_df['embeddings']])
                classifier_df = self.classifier_api.pp(embeddings=embeddings, artwork_id=self.artwork_id)
                self.combined_df = pl.concat([embeddings_df, colors_df.drop("artwork_id"), classifier_df.drop("artwork_id")], how="horizontal")
                self.combined_df.write_csv(self.csv_name)
            else:
                self.combined_df = pl.read_csv(self.csv_name)
            print(f"{len(self.combined_df)=}")

    async def get_ids_np(self, artwork_id):
        if self.real_api:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(
                    select(
                        ArtworkDB.embeddings,
                        ArtworkDB.colors,
                        ArtworkDB.abstract,
                        ArtworkDB.noisy,
                        ArtworkDB.paint
                    ).where(ArtworkDB.artwork_id.in_(artwork_id))
                )
                rows = result.all()

            embeddings = np.array([row[0] for row in rows])
            colors = np.array([row[1] for row in rows])
            abstract = np.array([row[2] for row in rows])
            noisy = np.array([row[3] for row in rows])
            paint = np.array([row[4] for row in rows])
            classifiers = np.stack([abstract, noisy, paint], axis=1)

            return dict(
                embeddings=embeddings,
                colors=colors,
                classifiers=classifiers,
                abstract=abstract,
                noisy=noisy,
                paint=paint
            )
        else:
            selected_rows = self.combined_df.filter(pl.col("artwork_id").is_in(artwork_id))
            return self._extract_np_from_rows(selected_rows)

    async def get_not_ids_np(self, artwork_id):
        if self.real_api:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(
                    select(
                        ArtworkDB.artwork_id,
                        ArtworkDB.embeddings,
                        ArtworkDB.colors,
                        ArtworkDB.abstract,
                        ArtworkDB.noisy,
                        ArtworkDB.paint
                    ).where(not_(ArtworkDB.artwork_id.in_(artwork_id)))
                )
                rows = result.all()

            ids = np.array([row[0] for row in rows])
            embeddings = np.array([row[1] for row in rows])
            colors = np.array([row[2] for row in rows])
            abstract = np.array([row[3] for row in rows])
            noisy = np.array([row[4] for row in rows])
            paint = np.array([row[5] for row in rows])
            classifiers = np.stack([abstract, noisy, paint], axis=1)

            return dict(
                ids=ids,
                embeddings=embeddings,
                colors=colors,
                classifiers=classifiers,
                abstract=abstract,
                noisy=noisy,
                paint=paint
            )
        else:
            selected_rows = self.combined_df.filter(~pl.col("artwork_id").is_in(artwork_id))
            data = self._extract_np_from_rows(selected_rows)
            data["ids"] = np.array(selected_rows['artwork_id'])
            return data

    async def get_all_ids_np(self):
        if self.real_api:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(select(ArtworkDB.artwork_id))
                return np.array([row[0] for row in result.all()])
        else:
            return np.array(self.combined_df['artwork_id'])

    async def get_pred_likes(self, artwork_id, sorted_indexes):
        if self.real_api:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(select(ArtworkDB.artwork_id).where(not_(ArtworkDB.artwork_id.in_(artwork_id))))
                artwork_ids = [row[0] for row in result.all()]
                sorted_artwork_id = [artwork_ids[i] for i in sorted_indexes]
                return sorted_artwork_id
        else:
            selected_rows = self.combined_df.filter(~pl.col("artwork_id").is_in(artwork_id))
            image_id_list = selected_rows["artwork_id"].to_list()
            sorted_artwork_id = [image_id_list[i] for i in sorted_indexes]
            return sorted_artwork_id

    def _extract_np_from_rows(self, rows):
        embeddings = np.array([json.loads(e) for e in rows['embeddings']])
        colors = np.array([json.loads(e) for e in rows['colors']])
        classifiers = np.array(rows.select([col for col in rows.columns if col in self.classifier_api.classes]))
        return dict(
            embeddings=embeddings,
            colors=colors,
            classifiers=classifiers,
            abstract=np.array(rows['abstract']),
            noisy=np.array(rows['noisy']),
            paint=np.array(rows['paint'])
        )

    def read_images_ids(self):
        return [img[:-4] for img in os.listdir(Config.images_folder) if img.endswith('.jpg')]

    async def add_artwork(self, artwork: Artwork):
        if not self.real_api:
            raise RuntimeError("Can only add artwork to DB in real_api=True mode.")
        
        async with self.AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.get(ArtworkDB, artwork.artwork_id)
                if result:
                    print(f"Artwork {artwork.artwork_id} already exists.")
                    return False

                colors = [self.colors_api.predict_from_path(path) for path in artwork.images]
                avg_color = np.mean(colors, axis=0)

                embeddings = [self.embeddings_api.predict_from_path(path) for path in artwork.images]
                avg_embedding = np.mean(embeddings, axis=0)

                classifier_preds = self.classifier_api.predict_from_embedding(avg_embedding)

                new_artwork = ArtworkDB(
                    artwork_id=artwork.artwork_id,
                    artist_id=artwork.artist_id,
                    artist_name=artwork.artist_name,
                    artwork_name=artwork.artwork_name,
                    images=artwork.images,
                    description=artwork.description or "",
                    category=artwork.category or "",
                    properties={
                        "media": artwork.media,
                        "medium": artwork.medium,
                        "size": artwork.size,
                        "price": artwork.price,
                        "styles": artwork.styles,
                        "subject": artwork.subject,
                    },
                    embeddings=avg_embedding.tolist(),
                    colors=avg_color.tolist(),
                    abstract=float(classifier_preds['abstract']),
                    noisy=float(classifier_preds['noisy']),
                    paint=float(classifier_preds['paint']),
                )
                print(f"classifier_preds={classifier_preds}")
                print(f"classifiers from new_artwork={new_artwork.abstract}, {new_artwork.noisy}, {new_artwork.paint}")
                session.add(new_artwork)
            await session.commit()
        return True
