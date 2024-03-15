/**
 * @file
 * This file is part of SeisSol.
 *
 * @author Stephanie Wollherr and Thomas Ulrich
 * @author Sebastian Wolf
 *
 * @section LICENSE
 * Copyright (c) 2014-2024, SeisSol Group
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 * 
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF  MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
*/


DefineConstant[lc_fault={250, Min 100, Max 5000, Name "lc_fault"}];

lc = 5 * lc_fault;
lc_nucl = 100;

Printf("%f", lc);
Printf("%f", lc_fault);
Printf("%f", lc_nucl);

Fault_length = 30e3;
Fault_width = 15e3;
Fault_dip = 60 * Pi/180.;
Stress_barrier = 13800.0;

// Nucleation in X,Z local coordinates
X_nucl = 0e3;
Width_nucl = 3e3;
Z_nucl = -12e3;

Xmax = 30e3;
Xmin = -Xmax;
Ymin = -Xmax + 0.5 * Fault_width * Cos(Fault_dip);
Ymax =  Xmax + 0.5 * Fault_width * Cos(Fault_dip);
Zmin = -Xmax;

// Create the Volume
Point(1) = {Xmin, Ymin, 0, lc};
Point(2) = {Xmin, Ymax, 0, lc};
Point(3) = {Xmax, Ymax, 0, lc};
Point(4) = {Xmax, Ymin, 0, lc};
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Curve Loop(5) = {1,2,3,4};
Plane Surface(1) = {5};
Extrude {0,0, Zmin} { Surface{1}; }

// Create the fault
Point(100) = {-0.5*Fault_length, -Fault_width * Cos(Fault_dip), -Fault_width * Sin(Fault_dip), lc};
Point(101) = {-0.5*Fault_length, -Stress_barrier * Cos(Fault_dip), -Stress_barrier * Sin(Fault_dip), lc};
Point(102) = {-0.5*Fault_length, 0, 0e3, lc};
Point(103) = {0.5*Fault_length, 0,  0e3, lc};
Point(104) = {0.5*Fault_length, -Stress_barrier * Cos(Fault_dip), -Stress_barrier * Sin(Fault_dip), lc};
Point(105) = {0.5*Fault_length, -Fault_width * Cos(Fault_dip), -Fault_width * Sin(Fault_dip), lc};

Line(100) = {100, 101};
Line(101) = {101, 102};
Line(102) = {102, 103};
Line(103) = {103, 104};
Line(104) = {104, 105};
Line(105) = {105, 100};
Line(150) = {101, 104};
Line{102} In Surface{1};

// Create nucleation patch
Point(200) = {X_nucl + 0.5*Width_nucl, (Z_nucl+0.5*Width_nucl)*Cos(Fault_dip), (Z_nucl+0.5*Width_nucl)*Sin(Fault_dip), lc_nucl};
Point(201) = {X_nucl - 0.5*Width_nucl, (Z_nucl+0.5*Width_nucl)*Cos(Fault_dip), (Z_nucl+0.5*Width_nucl)*Sin(Fault_dip), lc_nucl};
Point(202) = {X_nucl - 0.5*Width_nucl, (Z_nucl-0.5*Width_nucl)*Cos(Fault_dip), (Z_nucl-0.5*Width_nucl)*Sin(Fault_dip), lc_nucl};
Point(203) = {X_nucl + 0.5*Width_nucl, (Z_nucl-0.5*Width_nucl)*Cos(Fault_dip), (Z_nucl-0.5*Width_nucl)*Sin(Fault_dip), lc_nucl};
Line(200) = {200,201};
Line(201) = {201,202};
Line(202) = {202,203};
Line(203) = {203,200};
Line Loop(200) = {200,201,202,203};
Plane Surface(200) = {200};

Line Loop(101) = {101,102,103,-150,200,201,202,203};
Plane Surface(101) = {101};
Line Loop(102) = {100,150,104,105};
Plane Surface(102) = {102};

Surface{101,102,200} In Volume{1};

// There is a bug in "Attractor", we need to define a Ruled surface in FaceList
Line Loop(105) = {101,102,103,-150};
Ruled Surface(105) = {105};
Ruled Surface(106) = {102};
Ruled Surface(201) = {200};

// Managing coarsening away from the fault
// Attractor field returns the distance to the curve (actually, the
// distance to 100 equidistant points on the curve)
Field[1] = Distance;
Field[1].FacesList = {105,106};

Field[2] = Threshold;
Field[2].IField = 1;
Field[2].LcMin = lc_fault;
Field[2].LcMax = lc;
Field[2].DistMin = 3*Width_nucl;
Field[2].DistMax = 10*Width_nucl;

// Managing coarsening around the nucleation Patch
Field[3] = Distance;
Field[3].FacesList = {201};

Field[4] = Threshold;
Field[4].IField = 3;
Field[4].LcMin = lc_nucl;
Field[4].LcMax = lc_fault;
Field[4].DistMin = Width_nucl;
Field[4].DistMax = 3*Width_nucl;

Field[5] = Restrict;
Field[5].IField = 4;
Field[5].FacesList = {100,200} ;


Field[7] = Min;
Field[7].FieldsList = {2,5};

Background Field = 7;

Physical Surface(101) = {1};
Physical Surface(103) = {101,102,200};
Physical Surface(105) = {14,18,22,26,27};

Physical Volume(1) = {1};
