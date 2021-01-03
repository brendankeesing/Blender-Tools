Just a few small python scripts I've put together for Blender to help with various game dev needs.
I give no guarantee or stability or compatibility for any of these scripts.

# VertexPaintLayer.py

Provides a photoshop-style layer UI for vertex colors.

Features:
* Manage lots of vertex color layers on a single object
* Isolate layers
* Lots of blending options between layers
* Squash down to a single vertex channel
* All of Blender's built-in vertex color workflow remains unchanged

# WorldUVMap.py

Automatically unwrap UVs and scale so that 1 unit of UV is roughly 1 unit in world space.
The accuracy of the UV scales depends on how well seams have been placed.
This is super useful with rapidly prototyping environments as you can throw on basic textures and still get roughly good looking UVs.
