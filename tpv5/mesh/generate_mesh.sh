#!/bin/bash

for resolution in 5000 2000 300 
do
  echo $resolution
  gmsh -setnumber lc_fault $resolution -3 -algo hxt -o mesh_${resolution}.msh mesh.geo
  pumgen -s msh4 mesh_${resolution}.msh
done
