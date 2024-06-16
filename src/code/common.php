<?php
function getPopulations() {
	return [
		"ghs-pop",
		"gpw",
		"landscan",
		"worldpop",
	];	
}

function getAreas() {
	return [
		"urban",
		"urban-buffer",
		"urban-region",
	];
}

function getLimits() {
	return [
		20000,
		50000,
		250000,
		1000000,
	];
}

function findType($val) {
	$limits = getLimits();
	$val = round($val);
	foreach ($limits as $type => $limit) {
		if ($val < $limit) return $type;
	}
	return $type + 1;
}

function readCSV($filename, $key = NULL) {
	$file = fopen($filename, "r");
	if ($file === FALSE) {
		throw \Exception("Cannot open file {$filename}.");
	}
	$cols = NULL;
	$rows = [];
	while ($row = fgetcsv($file)) {
		if (empty($cols)) {
			$cols = $row;
			continue;
		}
		$row = array_combine($cols, $row);
		if (isset($key)) {
			$val = $row[$key];
			if (isset($rows[$val])) {
				throw \Exception("Duplicate key value {$val}.");
			}
			$rows[$val] = $row;			
		}
		else {
			$rows[] = $row;
		}
	}
	fclose($file);
	return $rows;
}

function saveCSV($filename, $rows) {
	$file = fopen($filename, "w");
	if ($file === FALSE) {
		throw \Exception("Cannot open file {$filename}.");
	}
	$cols = array_keys(reset($rows));
	fputcsv($file, $cols);
	foreach ($rows as $row) {
		$data = [];
		foreach ($cols as $col) {
			$data[$col] = $row[$col];
		}
		fputcsv($file, $data);
	}
	fclose($file);
}
?>