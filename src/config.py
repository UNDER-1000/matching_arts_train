class Config:
	noisy_model_path = "data/linear_regression_noise.pkl"
	abstract_model_path = "data/linear_regression_abstract.pkl"
	paint_model_path = "data/linear_regression_paint.pkl"
	colors_n_bins = 30
	supabase_password = "&6a*bFbMm$Ncb#q"
	db_url = f"postgresql+asyncpg://postgres.lkycsngpgfshrbnuviki:{supabase_password}@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"
	