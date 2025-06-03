export type ImageInfo = {
  path: string;
  name: string;
  id: number;
};

export type PredictRequest = {
  image_ids: number[];
  target: number[];
  embedding: number;
  color: number;
  abstract: number;
  noisy: number;
  paint: number;
};

export type PredictionFeedback = {
  prediction_session_id: string;
  feedback: Record<number, number>;
}; 