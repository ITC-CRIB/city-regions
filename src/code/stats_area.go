package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"math"
	"os"
)

const (
	EquatorialRadius = 6378137.0
	MeanRadius       = 6371008.8
	PolarRadius      = 6356752.3
)

// Calculates latitude-dependent mean radius
// https://rechneronline.de/earth-radius/
func meanRadius(rlat float64) float64 {
	sin := math.Sin(rlat)
	cos := math.Cos(rlat)
	a := EquatorialRadius * cos
	b := PolarRadius * sin
	c := a * EquatorialRadius
	d := b * PolarRadius
	return math.Sqrt((c * c + d * d) / (a * a + b * b))
}

func main() {
	w, h := 43200, 17400
	x0, y0 := -180.0, 84.9999420000000043
  dx, dy := 0.008333329999999999904, -0.008333329999999999904

	ids_filename := "L1_ID_1h_clipped_water.bil"
	var id_nodata int32 = -2147483648
	
	fmt.Printf("%d x %d grid, (%.2f, %2f: %.2f, %.2f)\n", w, h, x0, y0, dx, dy)
	
	ids := make([]int32, w * h)
	fmt.Printf("Reading %s...\n", ids_filename)
	{
		f, err := os.Open(ids_filename)
		defer f.Close()
		if err != nil {
			log.Fatal(err)
		}
		if err = binary.Read(f, binary.LittleEndian, ids); err != nil {
			log.Fatal(err)
		}
		if err = f.Close(); err != nil {
			log.Fatal(err)
		}
	}
	
	fmt.Printf("Processing...\n")
	total := 0.0
	nodata := 0
	sum := make(map[int32]float64)
	p := -1
	rdx := dx * math.Pi / 180
	rdy := dy * math.Pi / 180
	dxy := []float64{1, 0, 1, 1, 0, 1, 0, 0}
	for j := 0; j < h; j++ {
		// Calculate grid cell area in km2
		// https://www.movable-type.co.uk/scripts/latlong.html
		rx, ry := 0.0, (y0 + float64(j) * dy) * math.Pi / 180
		rx0, ry0 := rx, ry
		area := 0.0
		for k := 0; k < 8; k += 2 {
			rx1 := rx + dxy[k] * rdx
			ry1 := ry + dxy[k + 1] * rdy
			area += 2 * math.Atan2(math.Tan((rx1 - rx0) / 2) * (math.Tan(ry0 / 2) + math.Tan(ry1 / 2)), 1 + math.Tan(ry0 / 2) * math.Tan(ry1 / 2))
			rx0, ry0 = rx1, ry1
		}
		r := meanRadius(ry + rdy / 2)
		area = math.Abs(area * r * r) / 1e6
		/*
		if j > 0 && j % 10 == 0 {
			fmt.Printf("  %d/%d (%.2f km2)\n", j, h, area)
		}
		*/
		for i := 0; i < w; i++ {
			p++
			id := ids[p]
			if id == id_nodata {
				nodata++
				continue
			}
			total += area
			_, prs := sum[id]
			if prs {
				sum[id] += area
			} else {
				sum[id] = area
			}
		}
	}
	for id, area := range sum {
		fmt.Printf("%d\t%.2f\n", id, area)
	}
	fmt.Printf("Total area: %.2f\n", total)
	fmt.Printf("Number of data cells: %d\n", (w * h) - nodata)
	fmt.Printf("Number of no-data cells: %d\n", nodata)
}