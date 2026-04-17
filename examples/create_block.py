"""Example: Create a simple block using MCP tools.

This demonstrates the typical workflow:
1. Create a new part
2. Create a sketch on XY plane
3. Draw a rectangle
4. Finish sketch
5. Extrude the sketch
6. Save the part

Run via MCP client or directly with the MCP server.
"""

# These calls show what the AI agent would do via MCP:

# 1. nx_create_part(path="C:\\parts\\block.prt", units="mm")
#    → Created new part: block

# 2. nx_create_sketch(plane="XY", name="BaseSketch")
#    → Created sketch 'BaseSketch' on XY plane

# 3. nx_sketch_rectangle(x1=0, y1=0, x2=50, y2=30)
#    → Created rectangle 50.0x30.0 at (0,0)-(50,30)

# 4. nx_finish_sketch()
#    → Sketch finished — returned to modeling mode

# 5. nx_extrude(distance=20, direction="Z", boolean="none")
#    → Extrude created: EXTRUDE(0) (distance=20mm)

# 6. nx_blend(edges=["EDGE_0", "EDGE_1"], radius=3)
#    → Blend created: BLEND(1) (radius=3mm on 2 edge(s))

# 7. nx_save_part()
#    → Saved part: block

# 8. nx_set_view(orientation="isometric")
#    → View set to isometric

# 9. nx_screenshot(path="C:\\parts\\block_preview.png")
#    → Screenshot saved to C:\parts\block_preview.png

print(__doc__)
