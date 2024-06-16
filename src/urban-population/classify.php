<?php
require_once("../code/common.php");

$pops = getPopulations();

printf("Population datasets are %s.\n", implode(", ", $pops));

$area = $argv[1];
if (empty($area)) {
	echo "Please specify the area type.";
	exit(1);
}
echo "Area type is {$area}.\n";

$ref = $argv[2];
if (empty($ref)) {
	$ref = reset($pops);
}
else if (!in_array($ref, $pops)) {
	echo "Invalid reference population {$ref}.";
	exit(1);
}
echo "Reference population is {$ref}.\n";

$limit = count($pops) / 2;
printf("Limit is > %0.1f.\n", $limit);

echo "Reading population data...\n";
$data = readCSV("pop_{$area}.csv", "id");

echo "Classifying urban areas...\n";
ksort($data);
$file = fopen("type_{$area}.csv", "w");
fprintf($file, "id,%s,%s_type,min_type,max_type,common_type,type,state\n", implode(",", $pops), implode("_type,", $pops));
foreach ($data as $id => $vals) {
	$row = [$id];
	foreach ($pops as $key) {
		$row[] = round($vals[$key]);
	}
	$types = [];
	$count = [];
	foreach ($pops as $key) {
		$type = findType($vals[$key]);
		$row[] = $type;
		$count[$type]++;
		$types[$key] = $type;
	}
	$commons = array_keys($count, max($count));
	$common = max($commons);
	$state = 0;
	$min = min($types);
	$max = max($types);
	if ($min == $max) {
		$state = 1;
	}
	else if (max($count) > $limit) {
		$type = $common;
		$state = 2;
	}
	else if (in_array($types[$ref], $commons)) {
		$type = $types[$ref];
		$state = 3;
	}
	else if ($types[$ref] == $max) {
		$type = $max;
		$state = 4;
	}
	else if ($common > $types[$ref]) {
		$type = $common;
		$state = 5;
	}
	else {
		$type = $types[$ref];
		$state = 6;
	}
	$row[] = $min;
	$row[] = $max;
	$row[] = $common;
	$row[] = $type;
	$row[] = $state;
	fprintf($file, "%s\n", implode(",", $row));
}
fclose($file);
?>