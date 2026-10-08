For questions posed in part 1: It produces wrong area for Fiji because it crosses the antimeridian and shapely does not realize that this is same place on earth it treats it as distance on a normal cartesian grid which in this case will have the eastern half of Figi on the far left of the x axis on the grid.

Part 1 was an interesting lesson and made me review some core concepts. I did not know shapely would function that way for areas at the antimeridian. It is fun to explore these packages in this way. 

The agent initially clipped aoi geomtrey in 4326 which did not result in an error but ran successfully. I took several preliminary steps to ensure CRS would be handled appropriately. 1) I included the following instruction in AGENTS.md "Use the correct CRS and units for all spatial calculations. Confirm if unsure". 2) I instructed AGENT to produce a markdown report to summarize logic and procedure for handling coordinate reference systems. This was helpful and it was simple to fix issue. Obviously if clip a geomtery in units like degrees it will result in a different clip than if that polygon was projected to a crs in planar units like meters or feet. 3) I additionally pasted the new utility functions added to "utils.py" as well as code in "analysis.ipynb" into a google gemini window to help double check. This was helpful as a final validation to double check my own work. 

Crafting these AGENTS.md files is key to getting good results from the agentic coding. It can produce so much so quickly that without concise instructions the probabilty of de-railing and code making so sense has to be pretty high. I have actively tried to improve each AGENTS.md file as I work through these assignments that are increasing in complexity. 

Pasting output from "analysis.ipynb" file for context: 
AOI window read time: 16.355 seconds
Full red asset read time: 7.699 seconds

This is the opposite of what I expected as the AOI window is smaller and thus less pixels to read. However, the AOI window time read is more than double that of the full red asset time. This is probably due to the fact that were are comparing the read time of just 1 band for large region comapared against read time of two bands for small area resulting in longer read time for smaller region. This is an unfair comparison. I instructed agent to create a more comparable test comparing read time of NIR and RED for a small aoi and a large area, this results in are read time more in line with my expectations.

AOI Red + NIR window read time: 15.106 seconds
Full Red + NIR reference read time: 29.766 seconds

