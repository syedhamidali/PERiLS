'''
test_concurrent_griddding
'''
import parallel_gridding as pg
import concurrent.futures


nexrad_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/GRID/"
data_files = pg.get_nexrad_data_files("20220330220000", "20220331040000")

with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
    # Submit the tasks to the executor
    results = [executor.submit(pg.process_file, nexrad_dir, f) for f in data_files]
    # Wait for all tasks to complete
    concurrent.futures.wait(results)
