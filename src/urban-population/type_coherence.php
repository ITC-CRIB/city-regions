<?php
require_once("../code/common.php");

$areas = getAreas();

printf("Areas are %s.\n", implode(", ", $areas));

$data = [];
foreach ($areas as $area) {
	echo "Reading {$area} types...\n";
	$rows = readCSV("type_{$area}.csv", "id");
	foreach ($rows as $id => $row) {
		$data[$id][$area] = $row["type"];
	}
}
ksort($data);

echo "Writing types...\n";
$file = fopen("type.csv", "w");
fprintf($file, "id,%s\n", implode(",", $areas));
foreach ($data as $id => $vals) {
	$row = [$id];
	foreach ($areas as $area) {
		$row[] = $vals[$area];
	}
	fprintf($file, "%s\n", implode(",", $row));
}
fclose($file);

echo "Calculating coherence matrix...\n";
$matrix = [];
$n = count($areas);
foreach ($data as $id => $row) {
	$types = [];
	foreach ($areas as $area) {
		$types[] = $row[$area];
	}
	for ($i = 0; $i < $n; $i++) {
		$a = $areas[$i] . "_" . $types[$i];
		$matrix[$a][$a]++;
		for ($j = $i + 1; $j < $n; $j++) {
			$b = $areas[$j] . "_" . $types[$j];
			$matrix[$a][$b]++;
			$matrix[$b][$a]++;
		}
	}
}

echo "Writing coherence matrix...\n";
$keys = [];
foreach ($areas as $key) {
	for ($i = 0, $n = count(getLimits()); $i <= $n; $i++) {
		$keys[] = $key . "_" . $i;
	}
}
$file = fopen("type_coherence.csv", "w");
fprintf($file, "type,%s\n", implode(",", $keys));
foreach ($keys as $key) {
	$row = [$key];
	foreach ($keys as $otherKey) {
		$row[] = $matrix[$key][$otherKey];
	}
	fprintf($file, "%s\n", implode(",", $row));
}
fclose($file);
?>