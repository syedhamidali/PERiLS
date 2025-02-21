from distributed import Client, LocalCluster
import parallel_gridding as pg

cluster = LocalCluster()
client = Client(cluster)
# client

nexrad_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/"
data_files = pg.get_nexrad_data_files("20220330220000", "20220331040000")

# Create a list of tasks to process the data files
tasks = [client.submit(pg.process_file, nexrad_dir, f) for f in data_files]

# Gather the results of the tasks
results = client.gather(tasks)