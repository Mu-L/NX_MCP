"""Example: Create a simple assembly using MCP tools.

Workflow:
1. Create a new part for the base plate
2. Create a block (base plate)
3. Create a new part for the pin
4. Create a cylinder (pin)
5. Open the base part as assembly
6. Add pin as component
7. Mate the pin to the base plate
8. Save assembly

Run via MCP client or directly with the MCP server.
"""

# These calls show what the AI agent would do via MCP:

# 1. nx_create_part(path="C:\\parts\\base_plate.prt", units="mm")
# 2. nx_create_sketch(plane="XY", name="BaseSketch")
# 3. nx_sketch_rectangle(x1=-25, y1=-25, x2=25, y2=25)
# 4. nx_finish_sketch()
# 5. nx_extrude(distance=5, direction="Z")
# 6. nx_save_part()
#
# 7. nx_create_part(path="C:\\parts\\pin.prt", units="mm")
# 8. nx_sketch_arc(cx=0, cy=0, radius=3, start_angle=0, end_angle=360)
# 9. nx_finish_sketch()
# 10. nx_extrude(distance=20, direction="Z")
# 11. nx_save_part()
#
# 12. nx_open_part(path="C:\\parts\\base_plate.prt")
# 13. nx_add_component(part_path="C:\\parts\\pin.prt", name="pin_1")
# 14. nx_mate_component(component="pin_1", mate_type="align", references=["TOP_FACE", "HOLE_EDGE"])
# 15. nx_save_part()

print(__doc__)
