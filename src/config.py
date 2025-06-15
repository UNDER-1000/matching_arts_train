class Config:
	
	images_folder = 'data/data'
	csv_name = 'data/combined_df_data.csv'
	restart = False
	noisy_model_path = "data/linear_regression_noise.pkl"
	abstract_model_path = "data/linear_regression_abstract.pkl"
	paint_model_path = "data/linear_regression_paint.pkl"
	colors_n_bins = 30
	real_csv = 'data/combined_df_real.csv'
	supabase_password = "2Hk7nesuYJs1gl89"
	db_url = f"postgresql+asyncpg://postgres.mjrhmeyzwfttizwctiaf:{supabase_password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
	