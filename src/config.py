# class Config:
# 	noisy_model_path = "data/linear_regression_noise.pkl"
# 	abstract_model_path = "data/linear_regression_abstract.pkl"
# 	paint_model_path = "data/linear_regression_paint.pkl"
# 	walls_model_path = "wall_art_model.pt"
# 	colors_n_bins = 30

# 	db_name = "postgres"
# 	db_user_name="postgres"
# 	db_password=";-C/Ca@gbQ}*&g4s"
# 	db_host = "136.116.137.58"

# 	db_gcp_url = f"postgresql+asyncpg://{db_user_name}:{db_password}@{db_host}:5432/{db_name}"

# 	db_url = db_gcp_url
# 	# supabase_password = "&6a*bFbMm$Ncb#q"
# 	# db_url = f"postgresql+asyncpg://postgres.lkycsngpgfshrbnuviki:{supabase_password}@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"


# 	# walls_password = "YW79nvIlYkrCUAOd"
# 	# db_walls_url = f"postgresql+asyncpg://postgres.upuugapvaolengekcpqb:{walls_password}@aws-0-eu-north-1.pooler.supabase.com:6543/postgres"
# 	db_walls_url = db_gcp_url
# 	images_url = "https://storage.googleapis.com/image-matcher/artworks/"
# 	walls_url = "https://storage.googleapis.com/image-matcher/walls/"
	
class Config:
	noisy_model_path = "data/linear_regression_noise.pkl"
	abstract_model_path = "data/linear_regression_abstract.pkl"
	paint_model_path = "data/linear_regression_paint.pkl"
	walls_model_path = "wall_art_model.pt"
	colors_n_bins = 30

	db_name = "aiarts"
	db_user_name="moshe"
	db_password="~%GiYG7REj}s(hDh"
	db_host = "34.76.19.180"

	db_gcp_url = f"postgresql+asyncpg://{db_user_name}:{db_password}@{db_host}:5432/{db_name}"

	db_url = db_gcp_url
	# supabase_password = "&6a*bFbMm$Ncb#q"
	# db_url = f"postgresql+asyncpg://postgres.lkycsngpgfshrbnuviki:{supabase_password}@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"


	# walls_password = "YW79nvIlYkrCUAOd"
	# db_walls_url = f"postgresql+asyncpg://postgres.upuugapvaolengekcpqb:{walls_password}@aws-0-eu-north-1.pooler.supabase.com:6543/postgres"
	db_walls_url = db_gcp_url
	images_url = "https://storage.googleapis.com/image-matcher/artworks/"
	walls_url = "https://storage.googleapis.com/image-matcher/walls/"
	