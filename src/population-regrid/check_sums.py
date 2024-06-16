import rioxarray
import json
import gc

filename = "GHS_POP_E2020_GLOBE_R2022A_54009_1000_V1_0.tif"
delta = 100

sums = {}
with rioxarray.open_rasterio(filename, masked=True) as grid:
    for y in range(0, grid.sizes["y"], delta):
        part = grid.isel(y=slice(y, y+delta))
        sums[y] = part.sum().item(0)
with open('sums.json', 'w') as file:
    json.dump(sums, file)
sums

total = 0.0
for y, sum in sums.items():
    total += sum
print(total)

regrid_sums = {}
for y, sum in sums.items():
    filename = f"grid-{y}-{y+delta}.tif"
    with rioxarray.open_rasterio(filename, masked=True) as grid:
        regrid_sum = grid.sum(skipna=True).item(0)
        regrid_sums[y] = regrid_sum
    print(y, sum, regrid_sum)
    gc.collect()
with open('regrid_sums.json', 'w') as file:
    json.dump(regrid_sums, file)
sums
