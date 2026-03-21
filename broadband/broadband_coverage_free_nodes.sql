delete
from broadband_coverage_tree
where z > 10 and parent_x is null and parent_y is null;

delete
from broadband_coverage_tree_hyperfiber
where z > 10 and parent_x is null and parent_y is null;
