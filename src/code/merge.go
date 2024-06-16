package main

import (
	"bufio"
	"encoding/binary"
	"errors"
	"flag"
	"fmt"
	"log"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"sort"
)

/*
U1: 13001 - 31619
U2: 3001 - 12440
U3: 1001 - 2538
U4: 1 - 482
*/

const Levels = 4

type Metadata struct {
	w, h int
	noData float64
	filename string
	geoTransform string
}

type Record struct {
	Types [Levels]byte
	Ids [Levels]uint16
	Type uint16
}

func readMetadata(filename string) (Metadata, error) {
	var metadata Metadata

	exprs := map[string]string{
		"w": "(?i)rasterXSize=\"(\\d+)\"",
		"h": "(?i)rasterYSize=\"(\\d+)\"",
		"noData": "(?i)<NoDataValue>([^<]+)</NoDataValue>",
		"filename": "(?i)<SourceFilename[^>]+>([^<]+)</SourceFilename>",
		"geotransform": "(?i)<GeoTransform>([^<]+)</GeoTransform>",
	}

	content, err := os.ReadFile(filename)
	if err != nil {
		return metadata, err
	}
	text := string(content)

	for key, expr := range exprs {
		r, _ := regexp.Compile(expr)
		matches := r.FindStringSubmatch(text)
		if len(matches) < 2 || matches[1] == "" {
			return metadata, errors.New("Invalid VRT file")
		}
		val := matches[1]
		switch key {
		case "w":
			metadata.w, err = strconv.Atoi(val)
			if err != nil || metadata.w <= 0 {
				return metadata, errors.New("Invalid raster width")
			}
		case "h":
			metadata.h, err = strconv.Atoi(val)
			if err != nil || metadata.h <= 0 {
				return metadata, errors.New("Invalid raster height")
			}
		case "noData":
			metadata.noData, err = strconv.ParseFloat(val, 64)
			if err != nil {
				return metadata, errors.New("Invalid no data value")
			}
		case "filename":
			metadata.filename = val
		case "geotransform":
			metadata.geoTransform = val
		}

	}

	return metadata, nil
}

func main() {
	const MaxBits = 64
	const MantissaBits = 52

	// Data path
	var path string

	// Grid dimensions
	var w, h int

	// Travel time threshold (min)
	var threshold float64

	// No data value
	var noData int

	// Affine geotransformation
	var geoTransform string

	flag.Float64Var(&threshold, "threshold", 0.0, "travel time threshold (min)")
	flag.IntVar(&noData, "nodata", 0, "no data value")

	flag.Parse()

	// Data path
	path = flag.Arg(0)
	if path == "" {
		fmt.Println("Please enter the data path.")
		os.Exit(1)
	}

	fmt.Printf("Loading data from %s.\n", path)
	fmt.Printf("No data value is %d.\n", noData)
	if threshold > 0.0 {
		fmt.Printf("Travel time threshold is %0.2f.\n", threshold)
	} else {
		fmt.Printf("No travel time threshold.\n")
	}

	var grids [Levels][]uint16
	var offsets [Levels]int
	var maxs [Levels]uint16

	offset := 0
	for i := 0; i < Levels; i++ {
		level := i + 1

		filename := fmt.Sprintf("L%d_id.vrt", level)
		fmt.Printf("Loading level %d from %s.\n", level, filename)
		metadata, err := readMetadata(filepath.Join(path, filename))
		if err != nil {
			log.Fatal(err)
		}
		if w == 0 || h == 0 {
			w, h = metadata.w, metadata.h
			geoTransform = metadata.geoTransform
		} else if w != metadata.w || h != metadata.h {
			fmt.Printf("Grid size %d x %d does not match %d x %d.", metadata.w, metadata.h, w, h)
			os.Exit(1)
		}

		grids[i] = make([]uint16, metadata.w * metadata.h)
		offsets[i] = offset

		file, err := os.Open(filepath.Join(path, metadata.filename))
		if err != nil {
			log.Fatal(err)
		}
		defer file.Close()
		err = binary.Read(file, binary.LittleEndian, grids[i])
		if err != nil {
			log.Fatal(err)
		}
		err = file.Close()
		if err != nil {
			log.Fatal(err)
		}

		if threshold > 0.0 {
			filename := fmt.Sprintf("L%d_sum.vrt", level)
			fmt.Printf("Loading travel time for level %d from %s...\n", level, filename)

			metadata, err := readMetadata(filepath.Join(path, filename))
			if err != nil {
				log.Fatal(err)
			}
			if w != metadata.w || h != metadata.h {
				fmt.Printf("Grid size %d x %d does not match %d x %d.\n", metadata.w, metadata.h, w, h)
				os.Exit(1)
			}

			times := make([]float32, metadata.w * metadata.h)
			file, err := os.Open(filepath.Join(path, metadata.filename))
			if err != nil {
				log.Fatal(err)
			}
			defer file.Close()
			err = binary.Read(file, binary.LittleEndian, times)
			if err != nil {
				log.Fatal(err)
			}
			err = file.Close()
			if err != nil {
				log.Fatal(err)
			}
			fmt.Printf("Applying travel time threshold %0.2f for level %d\n", threshold, level)
			for idx, _ := range grids[i] {
				if times[idx] > float32(threshold) {
					grids[i][idx] = uint16(noData)
				}
			}
			times = nil
			runtime.GC()
		}

		max := uint16(0)
		for _, v := range grids[i] {
			if v > max {
				max = v
			}
		}
		bits := 1
		for val := 1; val < int(max); val = 1 << bits {
			bits++
		}
		fmt.Printf("Maximum value for level %d is %d, %d bits required.\n", level, max, bits)
		offset += bits
		maxs[i] = max
	}

	fmt.Printf("Offsets are %v.\n", offsets)
	if offset > MaxBits {
		log.Fatalf("Number of required bits %d is more than the maximum %d.", offset, MaxBits)
	}
	if offset > MantissaBits {
		fmt.Printf("WARNING: Number of requires bits %d is more than mantissa bits %d.\n", offset, MantissaBits)
	}

	size := w * h
	grid := make([]float64, size)

	var types [Levels]byte
	var ids[Levels]uint16

	records := make(map[uint64]Record)

	fmt.Printf("Combining levels.\n")
	for idx := 0; idx < size; idx++ {
		for i := 0; i < Levels; i++ {
			val := grids[i][idx]
			if val == 0 {
				types[i] = 0
			} else if val <= maxs[3] {
				types[i] = 4
			} else if val <= maxs[2] {
				types[i] = 3
			} else if val <= maxs[1] {
				types[i] = 2
			} else {
				types[i] = 1
			}
			ids[i] = val
		}
		id :=
			uint64(uint64(grids[0][idx]) << offsets[0]) +
			uint64(uint64(grids[1][idx]) << offsets[1]) +
			uint64(uint64(grids[2][idx]) << offsets[2]) +
			uint64(uint64(grids[3][idx]) << offsets[3])
		grid[idx] = float64(id)
		if id != 0 {
			_, found := records[id]
			if !found {
				records[id] = Record{
					Types: types,
					Ids: ids,
					Type: uint16(types[3]) + uint16(types[2]) * 10 + uint16(types[1]) * 100 + uint16(types[0]) * 1000,
				}
			}
		}
	}

	var filename string
	if threshold > 0.0 {
		filename = fmt.Sprintf("City_Regions_%0.2f", threshold)
	} else {
		filename = "City_Regions"
	}
	fmt.Printf("Saving combined grid as %s...\n", filename)

	// Store grid metadata
	vrt := fmt.Sprintf(
		"<VRTDataset rasterXSize=\"%d\" rasterYSize=\"%d\">\n" +
		"<GeoTransform>%s</GeoTransform>\n" +
		"<VRTRasterBand dataType=\"Float64\" band=\"1\" blockYSize=\"1\" subClass=\"VRTRawRasterBand\">\n" +
    "<NoDataValue>%d</NoDataValue>\n" +
    "<SourceFilename relativeToVRT=\"1\">%s</SourceFilename>\n" +
    "<ImageOffset>0</ImageOffset>\n" +
    "<PixelOffset>8</PixelOffset>\n" +
    "<LineOffset>%d</LineOffset>\n" +
    "<ByteOrder>LSB</ByteOrder>\n" +
		"</VRTRasterBand>\n" +
		"</VRTDataset>",
		w, h, geoTransform, noData, filename + ".img", w * 8,
	)
	file, err := os.Create(filepath.Join(path, filename + ".vrt"))
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	_, err = file.WriteString(vrt)
	if err != nil {
		log.Fatal(err)
	}
	err = file.Close()
	if err != nil {
		log.Fatal(err)
	}

	// Store grid data
	buf := make([]byte, 8)
	file, err = os.Create(filepath.Join(path, filename + ".img"))
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	writer := bufio.NewWriter(file)
	defer writer.Flush()
	for _, v := range grid {
		binary.LittleEndian.PutUint64(buf, math.Float64bits(v))
		_, err = writer.Write(buf)
		if err != nil {
			log.Fatal(err)
		}
	}
	err = writer.Flush()
	if err != nil {
		log.Fatal(err)
	}
	err = file.Close()
	if err != nil {
		log.Fatal(err)
	}

	// Store record table
	keys := make([]uint64, len(records))
	i := 0
	for key, _ := range records {
		keys[i] = key
		i++
	}
	sort.Slice(keys, func(i, j int) bool {
		return keys[i] < keys[j]
	})

	file, err = os.Create(filepath.Join(path, filename + ".csv"))
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	writer = bufio.NewWriter(file)
	defer writer.Flush()

	writer.WriteString("id,type,L1_id,L2_id,L3_id,L4_id,L1_type,L2_tpe,L3_type,L4_type\n")
	for _, key := range keys {
		record := records[key]
		row := fmt.Sprintf(
			"%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
			key,
			record.Type,
			record.Ids[0], record.Ids[1], record.Ids[2], record.Ids[3],
			record.Types[0], record.Types[1], record.Types[2], record.Types[3],
		)
		writer.WriteString(row)
	}
	err = writer.Flush()
	if err != nil {
		log.Fatal(err)
	}
	err = file.Close()
	if err != nil {
		log.Fatal(err)
	}
}