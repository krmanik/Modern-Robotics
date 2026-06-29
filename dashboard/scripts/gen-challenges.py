#!/usr/bin/env python3
"""Author Modern Robotics coding challenges. Reference solutions are pure-python
so expected outputs are computed here and embedded -> src/lib/data/challenges.json"""
import json, math, os

CH = {}
def add(chap, **kw): CH.setdefault(chap, []).append(kw)

# ============================ reference solutions ============================
def grubler(m, N, J, fs): return m * (N - 1 - J) + sum(fs)
def redundancy(dof, task): return dof - task
def free_bodies_dof(m, n): return m * n

def vec_to_so3(w): return [[0,-w[2],w[1]],[w[2],0,-w[0]],[-w[1],w[0],0]]
def so3_to_vec(M): return [M[2][1], M[0][2], M[1][0]]
def rot_inv(R): return [[R[j][i] for j in range(3)] for i in range(3)]
def rot2(t): c,s=math.cos(t),math.sin(t); return [[c,-s],[s,c]]
def rotz(t): c,s=math.cos(t),math.sin(t); return [[c,-s,0],[s,c,0],[0,0,1]]
def matmul3(A,B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def rot_angle(R):
    tr = R[0][0]+R[1][1]+R[2][2]
    return math.acos(max(-1.0, min(1.0, (tr-1)/2)))

def trans_inv(T):
    R=[[T[i][j] for j in range(3)] for i in range(3)]; p=[T[i][3] for i in range(3)]
    Rt=[[R[j][i] for j in range(3)] for i in range(3)]
    q=[-sum(Rt[i][k]*p[k] for k in range(3)) for i in range(3)]
    return [Rt[0]+[q[0]],Rt[1]+[q[1]],Rt[2]+[q[2]],[0,0,0,1]]
def rp_to_trans(R,p): return [R[0]+[p[0]],R[1]+[p[1]],R[2]+[p[2]],[0,0,0,1]]
def trans_to_rp(T): return [[[T[i][j] for j in range(3)] for i in range(3)],[T[i][3] for i in range(3)]]
def fk_2r(L1,L2,t1,t2): return [L1*math.cos(t1)+L2*math.cos(t1+t2), L1*math.sin(t1)+L2*math.sin(t1+t2)]
def fk_3r(L1,L2,L3,t1,t2,t3):
    a,b,c=t1,t1+t2,t1+t2+t3
    return [L1*math.cos(a)+L2*math.cos(b)+L3*math.cos(c), L1*math.sin(a)+L2*math.sin(b)+L3*math.sin(c), c]

def jacobian_2r(L1,L2,t1,t2):
    s1,c1=math.sin(t1),math.cos(t1); s12,c12=math.sin(t1+t2),math.cos(t1+t2)
    return [[-L1*s1-L2*s12,-L2*s12],[L1*c1+L2*c12,L2*c12]]
def det2(J): return J[0][0]*J[1][1]-J[0][1]*J[1][0]
def manipulability(J): return abs(det2(J))
def is_singular(J): return abs(det2(J)) < 1e-9
def joint_torques(J,F): return [J[0][0]*F[0]+J[1][0]*F[1], J[0][1]*F[0]+J[1][1]*F[1]]

def ik_2r_th2(L1,L2,x,y):
    c2=max(-1.0,min(1.0,(x*x+y*y-L1*L1-L2*L2)/(2*L1*L2))); return math.acos(c2)
def ik_reachable(L1,L2,x,y):
    r=math.hypot(x,y); return abs(L1-L2)-1e-9 <= r <= L1+L2+1e-9
def law_of_cosines(a,b,c):
    return math.acos(max(-1.0,min(1.0,(a*a+b*b-c*c)/(2*a*b))))

def joint_torque(I,ddth,m,g,l,th): return I*ddth + m*g*l*math.sin(th)
def kinetic_energy(M,v): return 0.5*sum(v[i]*M[i][j]*v[j] for i in range(len(v)) for j in range(len(v)))
def rotational_ke(I,w): return 0.5*I*w*w

def cubic(Tf,t): a=t/Tf; return 3*a**2-2*a**3
def cubic_dot(Tf,t): a=t/Tf; return (6/Tf)*a*(1-a)
def quintic(Tf,t): a=t/Tf; return 10*a**3-15*a**4+6*a**5
def straight_line(start,end,s): return [start[i]+s*(end[i]-start[i]) for i in range(len(start))]

def grid_neighbors(r,c,rows,cols):
    out=[]
    for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr,nc=r+dr,c+dc
        if 0<=nr<rows and 0<=nc<cols: out.append([nr,nc])
    return sorted(out)
def manhattan(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
def euclidean(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def chebyshev(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]))

def pid(Kp,Ki,Kd,e,edot,eint): return Kp*e+Ki*eint+Kd*edot
def pd_control(Kp,Kd,th,thd,th_d,thd_d): return Kp*(th_d-th)+Kd*(thd_d-thd)
def stable(Kp,Kd): return Kp>0 and Kd>0
def damping_type(zeta):
    if abs(zeta-1)<1e-9: return "critically damped"
    return "overdamped" if zeta>1 else "underdamped"

def friction_cone_angle(mu): return math.atan(mu)
def in_friction_cone(mu,fn,ft): return abs(ft) <= mu*fn
def min_contacts_form_closure(planar): return 4 if planar else 7
def contact_wrench(fx,fy,px,py): return [px*fy-py*fx, fx, fy]

def diff_drive(r,L,uL,uR): return [r*(uR-uL)/L, r*(uR+uL)/2, 0]
def wheel_speeds_diff(v,w,r,L): return [(2*v-w*L)/(2*r),(2*v+w*L)/(2*r)]
def unicycle_step(x,y,phi,v,w,dt): return [x+v*math.cos(phi)*dt, y+v*math.sin(phi)*dt, phi+w*dt]

# ============================ challenge catalogue ============================
PI=math.pi
def C(chap,id,title,diff,func,tags,prompt,starter,sol,ref,args):
    add(chap,id=id,title=title,difficulty=diff,func=func,tags=tags,prompt=prompt,starter=starter,sol=sol,ref=ref,args=args)

# ---- Ch2: Configuration Space ----
C('ch02','ch02-grubler',"Degrees of Freedom (Grübler)",'Easy','grubler',['mobility'],
 "Grübler's formula gives the DOF of a mechanism:\n\n    dof = m·(N − 1 − J) + Σ fᵢ\n\nm is the DOF of one rigid body (3 planar, 6 spatial), N is the number of links *including ground*, J the number of joints, and `fs` lists each joint's freedoms.\n\nImplement `grubler(m, N, J, fs)`.",
 "def grubler(m, N, J, fs):\n    pass\n",grubler,
 "def grubler(m, N, J, fs):\n    return m * (N - 1 - J) + sum(fs)\n",
 [[3,4,4,[1,1,1,1]],[6,4,3,[1,1,1]],[3,5,5,[1,1,1,1,1]],[6,8,9,[1,1,1,1,1,1,1,1,1]]])

C('ch02','ch02-spatial-chain',"Spatial Open-Chain DOF",'Easy','grubler',['mobility'],
 "An open chain of N links (incl. ground) joined by N−1 single-DOF revolute joints in space (m=6) has exactly N−1 DOF. Use the same `grubler(m, N, J, fs)` to confirm it.",
 "def grubler(m, N, J, fs):\n    pass\n",grubler,
 "def grubler(m, N, J, fs):\n    return m * (N - 1 - J) + sum(fs)\n",
 [[6,7,6,[1,1,1,1,1,1]],[6,3,2,[1,1]]])

C('ch02','ch02-redundancy',"Degree of Redundancy",'Easy','redundancy',['workspace'],
 "A robot with `dof` joints performing a task that needs `task` dimensions has redundancy = dof − task (when positive, infinitely many joint solutions reach a goal).\n\nImplement `redundancy(dof, task)`.",
 "def redundancy(dof, task):\n    pass\n",redundancy,
 "def redundancy(dof, task):\n    return dof - task\n",
 [[7,6],[6,6],[4,3]])

C('ch02','ch02-freebodies',"DOF of Free Rigid Bodies",'Easy','free_bodies_dof',['cspace'],
 "n unconstrained rigid bodies each have m DOF, so together m·n. Implement `free_bodies_dof(m, n)`.",
 "def free_bodies_dof(m, n):\n    pass\n",free_bodies_dof,
 "def free_bodies_dof(m, n):\n    return m * n\n",
 [[6,1],[3,4],[6,5]])

# ---- Ch3: Rigid-Body Motions ----
C('ch03','ch03-skew',"Skew-Symmetric Matrix [ω]",'Easy','vec_to_so3',['so3'],
 "Map ω = (ω₁,ω₂,ω₃) to [ω] ∈ so(3):\n\n    [ω] = [[0,−ω₃,ω₂],[ω₃,0,−ω₁],[−ω₂,ω₁,0]]\n\nImplement `vec_to_so3(w)`.",
 "def vec_to_so3(w):\n    pass\n",vec_to_so3,
 "def vec_to_so3(w):\n    return [[0,-w[2],w[1]],\n            [w[2],0,-w[0]],\n            [-w[1],w[0],0]]\n",
 [[[1,2,3]],[[0,0,1]],[[-2,5,0]]])

C('ch03','ch03-unskew',"Vector from [ω] (so3→vec)",'Easy','so3_to_vec',['so3'],
 "Recover ω from a skew-symmetric matrix: ω = (M₂₁, M₀₂, M₁₀).\n\nImplement `so3_to_vec(M)` (3×3 list → 3-vector).",
 "def so3_to_vec(M):\n    pass\n",so3_to_vec,
 "def so3_to_vec(M):\n    return [M[2][1], M[0][2], M[1][0]]\n",
 [[[[0,-3,2],[3,0,-1],[-2,1,0]]],[[[0,0,0],[0,0,-1],[0,1,0]]]])

C('ch03','ch03-rotinv',"Inverse of a Rotation Matrix",'Easy','rot_inv',['so3'],
 "For R ∈ SO(3), R⁻¹ = Rᵀ. Implement `rot_inv(R)` returning the transpose of the 3×3 matrix.",
 "def rot_inv(R):\n    pass\n",rot_inv,
 "def rot_inv(R):\n    return [[R[j][i] for j in range(3)] for i in range(3)]\n",
 [[[[1,0,0],[0,1,0],[0,0,1]]],[[[0,-1,0],[1,0,0],[0,0,1]]]])

C('ch03','ch03-rot2',"Planar Rotation Matrix",'Easy','rot2',['so3'],
 "The 2×2 rotation by angle θ is [[cosθ,−sinθ],[sinθ,cosθ]].\n\nImplement `rot2(t)`.",
 "import math\n\ndef rot2(t):\n    pass\n",rot2,
 "import math\n\ndef rot2(t):\n    c, s = math.cos(t), math.sin(t)\n    return [[c, -s], [s, c]]\n",
 [[0],[PI/2],[PI]])

C('ch03','ch03-rotz',"Rotation about ẑ (Rz)",'Easy','rotz',['so3'],
 "Rz(θ) = [[c,−s,0],[s,c,0],[0,0,1]] with c=cosθ, s=sinθ.\n\nImplement `rotz(t)`.",
 "import math\n\ndef rotz(t):\n    pass\n",rotz,
 "import math\n\ndef rotz(t):\n    c, s = math.cos(t), math.sin(t)\n    return [[c,-s,0],[s,c,0],[0,0,1]]\n",
 [[0],[PI/2]])

C('ch03','ch03-matmul',"3×3 Matrix Multiply",'Medium','matmul3',['linalg'],
 "Composing rotations is matrix multiplication. Implement `matmul3(A, B)` for two 3×3 matrices (no numpy).",
 "def matmul3(A, B):\n    pass\n",matmul3,
 "def matmul3(A, B):\n    return [[sum(A[i][k]*B[k][j] for k in range(3))\n             for j in range(3)] for i in range(3)]\n",
 [[[[1,0,0],[0,1,0],[0,0,1]],[[1,2,3],[4,5,6],[7,8,9]]],
  [[[0,-1,0],[1,0,0],[0,0,1]],[[0,-1,0],[1,0,0],[0,0,1]]]])

C('ch03','ch03-angle',"Rotation Angle from R",'Medium','rot_angle',['exp-coords'],
 "The exponential-coordinate angle of R ∈ SO(3) is θ = arccos((tr R − 1)/2). Clamp the argument to [−1,1].\n\nImplement `rot_angle(R)`.",
 "import math\n\ndef rot_angle(R):\n    pass\n",rot_angle,
 "import math\n\ndef rot_angle(R):\n    tr = R[0][0]+R[1][1]+R[2][2]\n    return math.acos(max(-1.0, min(1.0, (tr-1)/2)))\n",
 [[[[1,0,0],[0,1,0],[0,0,1]]],[[[0,-1,0],[1,0,0],[0,0,1]]],[[[-1,0,0],[0,-1,0],[0,0,1]]]])

# ---- Ch4: Forward Kinematics ----
C('ch04','ch04-transinv',"Inverse of a Homogeneous Transform",'Medium','trans_inv',['se3'],
 "T = [[R,p],[0,1]] ∈ SE(3) has inverse [[Rᵀ,−Rᵀp],[0,1]].\n\nImplement `trans_inv(T)` for a 4×4 list.",
 "def trans_inv(T):\n    pass\n",trans_inv,
 "def trans_inv(T):\n    R=[[T[i][j] for j in range(3)] for i in range(3)]\n    p=[T[i][3] for i in range(3)]\n    Rt=[[R[j][i] for j in range(3)] for i in range(3)]\n    q=[-sum(Rt[i][k]*p[k] for k in range(3)) for i in range(3)]\n    return [Rt[0]+[q[0]],Rt[1]+[q[1]],Rt[2]+[q[2]],[0,0,0,1]]\n",
 [[[[1,0,0,3],[0,1,0,-2],[0,0,1,5],[0,0,0,1]]],[[[0,-1,0,1],[1,0,0,2],[0,0,1,3],[0,0,0,1]]]])

C('ch04','ch04-rptotrans',"Build Transform from (R, p)",'Easy','rp_to_trans',['se3'],
 "Assemble T = [[R,p],[0,1]] from a 3×3 R and 3-vector p.\n\nImplement `rp_to_trans(R, p)`.",
 "def rp_to_trans(R, p):\n    pass\n",rp_to_trans,
 "def rp_to_trans(R, p):\n    return [R[0]+[p[0]], R[1]+[p[1]], R[2]+[p[2]], [0,0,0,1]]\n",
 [[[[1,0,0],[0,1,0],[0,0,1]],[3,4,5]],[[[0,-1,0],[1,0,0],[0,0,1]],[1,2,3]]])

C('ch04','ch04-transtorp',"Split Transform into (R, p)",'Easy','trans_to_rp',['se3'],
 "Extract the rotation and translation from a 4×4 T. Return `[R, p]` where R is 3×3 and p is a 3-vector.\n\nImplement `trans_to_rp(T)`.",
 "def trans_to_rp(T):\n    pass\n",trans_to_rp,
 "def trans_to_rp(T):\n    R = [[T[i][j] for j in range(3)] for i in range(3)]\n    p = [T[i][3] for i in range(3)]\n    return [R, p]\n",
 [[[[1,0,0,7],[0,1,0,8],[0,0,1,9],[0,0,0,1]]]])

C('ch04','ch04-fk2r',"Planar 2R Forward Kinematics",'Easy','fk_2r',['poe'],
 "Planar 2R arm: x = L1c1 + L2c12, y = L1s1 + L2s12 (c12 = cos(θ1+θ2)).\n\nImplement `fk_2r(L1, L2, t1, t2)` → [x, y].",
 "import math\n\ndef fk_2r(L1, L2, t1, t2):\n    pass\n",fk_2r,
 "import math\n\ndef fk_2r(L1, L2, t1, t2):\n    return [L1*math.cos(t1)+L2*math.cos(t1+t2),\n            L1*math.sin(t1)+L2*math.sin(t1+t2)]\n",
 [[1,1,0,0],[1,1,PI/2,0],[2,1,PI/2,PI/2]])

C('ch04','ch04-fk3r',"Planar 3R Forward Kinematics",'Medium','fk_3r',['poe'],
 "Planar 3R arm end-effector pose is [x, y, φ] with φ = θ1+θ2+θ3 and x,y the chained link tips.\n\nImplement `fk_3r(L1, L2, L3, t1, t2, t3)`.",
 "import math\n\ndef fk_3r(L1, L2, L3, t1, t2, t3):\n    pass\n",fk_3r,
 "import math\n\ndef fk_3r(L1, L2, L3, t1, t2, t3):\n    a, b, c = t1, t1+t2, t1+t2+t3\n    x = L1*math.cos(a)+L2*math.cos(b)+L3*math.cos(c)\n    y = L1*math.sin(a)+L2*math.sin(b)+L3*math.sin(c)\n    return [x, y, c]\n",
 [[1,1,1,0,0,0],[1,1,1,PI/2,0,0],[1,1,1,PI/2,PI/2,PI/2]])

# ---- Ch5: Velocity Kinematics ----
C('ch05','ch05-jac2r',"Planar 2R Jacobian",'Medium','jacobian_2r',['jacobian'],
 "J = [[−L1s1−L2s12, −L2s12],[L1c1+L2c12, L2c12]].\n\nImplement `jacobian_2r(L1, L2, t1, t2)` (2×2).",
 "import math\n\ndef jacobian_2r(L1, L2, t1, t2):\n    pass\n",jacobian_2r,
 "import math\n\ndef jacobian_2r(L1, L2, t1, t2):\n    s1,c1=math.sin(t1),math.cos(t1)\n    s12,c12=math.sin(t1+t2),math.cos(t1+t2)\n    return [[-L1*s1-L2*s12,-L2*s12],[L1*c1+L2*c12,L2*c12]]\n",
 [[1,1,0,0],[1,1,PI/2,PI/2]])

C('ch05','ch05-det',"2×2 Determinant",'Easy','det2',['jacobian'],
 "Implement `det2(J)` = J₀₀·J₁₁ − J₀₁·J₁₀.",
 "def det2(J):\n    pass\n",det2,
 "def det2(J):\n    return J[0][0]*J[1][1]-J[0][1]*J[1][0]\n",
 [[[[1,0],[0,1]]],[[[2,3],[4,6]]],[[[0,-1],[1,0]]]])

C('ch05','ch05-singular',"Detect a Singularity",'Easy','is_singular',['singularity'],
 "A 2×2 Jacobian is singular when |det J| < 1e-9. Implement `is_singular(J)` → bool.",
 "def is_singular(J):\n    pass\n",is_singular,
 "def is_singular(J):\n    d = J[0][0]*J[1][1]-J[0][1]*J[1][0]\n    return abs(d) < 1e-9\n",
 [[[[1,0],[0,1]]],[[[2,3],[4,6]]]])

C('ch05','ch05-manip',"Manipulability Measure",'Medium','manipulability',['manipulability'],
 "For a square Jacobian, the manipulability μ = √(det(JJᵀ)) = |det J|.\n\nImplement `manipulability(J)` for a 2×2 J.",
 "def manipulability(J):\n    pass\n",manipulability,
 "def manipulability(J):\n    return abs(J[0][0]*J[1][1]-J[0][1]*J[1][0])\n",
 [[[[1,0],[0,1]]],[[[1,2],[3,4]]]])

C('ch05','ch05-statics',"Statics: Joint Torques τ = JᵀF",'Medium','joint_torques',['statics'],
 "Static equilibrium maps an end-effector wrench F to joint torques τ = Jᵀ F. For a 2×2 J and 2-vector F, return [τ1, τ2].\n\nImplement `joint_torques(J, F)`.",
 "def joint_torques(J, F):\n    pass\n",joint_torques,
 "def joint_torques(J, F):\n    return [J[0][0]*F[0]+J[1][0]*F[1],\n            J[0][1]*F[0]+J[1][1]*F[1]]\n",
 [[[[1,0],[0,1]],[5,7]],[[[0,-1],[1,0]],[2,3]]])

# ---- Ch6: Inverse Kinematics ----
C('ch06','ch06-ik2r',"IK: Elbow Angle",'Medium','ik_2r_th2',['analytic-ik'],
 "cosθ2 = (x²+y²−L1²−L2²)/(2L1L2); θ2 = arccos(clamp(cosθ2)). Implement `ik_2r_th2(L1, L2, x, y)`.",
 "import math\n\ndef ik_2r_th2(L1, L2, x, y):\n    pass\n",ik_2r_th2,
 "import math\n\ndef ik_2r_th2(L1, L2, x, y):\n    c2=(x*x+y*y-L1*L1-L2*L2)/(2*L1*L2)\n    return math.acos(max(-1.0,min(1.0,c2)))\n",
 [[1,1,1,1],[1,1,2,0],[2,1,3,0]])

C('ch06','ch06-reach',"Is the Target Reachable?",'Easy','ik_reachable',['analytic-ik'],
 "A planar 2R arm reaches (x,y) iff |L1−L2| ≤ √(x²+y²) ≤ L1+L2.\n\nImplement `ik_reachable(L1, L2, x, y)` → bool.",
 "import math\n\ndef ik_reachable(L1, L2, x, y):\n    pass\n",ik_reachable,
 "import math\n\ndef ik_reachable(L1, L2, x, y):\n    r=math.hypot(x,y)\n    return abs(L1-L2)-1e-9 <= r <= L1+L2+1e-9\n",
 [[1,1,1,1],[1,1,3,0],[2,1,0.5,0]])

C('ch06','ch06-loc',"Law of Cosines (angle)",'Easy','law_of_cosines',['analytic-ik'],
 "Angle opposite side c in a triangle with sides a,b,c: γ = arccos((a²+b²−c²)/(2ab)).\n\nImplement `law_of_cosines(a, b, c)`.",
 "import math\n\ndef law_of_cosines(a, b, c):\n    pass\n",law_of_cosines,
 "import math\n\ndef law_of_cosines(a, b, c):\n    return math.acos(max(-1.0,min(1.0,(a*a+b*b-c*c)/(2*a*b))))\n",
 [[1,1,1],[3,4,5],[2,2,2]])

# ---- Ch7: Closed Chains ----
C('ch07','ch07-stewart',"Stewart Platform Mobility",'Medium','grubler',['parallel'],
 "The 6-UPS Stewart platform: m=6, N=14 links, J=18 joints, each leg's joints contribute 2+1+3 freedoms. Use `grubler(m, N, J, fs)`; the result should be 6.",
 "def grubler(m, N, J, fs):\n    pass\n",grubler,
 "def grubler(m, N, J, fs):\n    return m * (N - 1 - J) + sum(fs)\n",
 [[6,14,18,[2,1,3]*6]])

C('ch07','ch07-3rrr',"Planar 3-RRR Parallel Robot",'Medium','grubler',['parallel'],
 "A planar 3-RRR parallel manipulator has m=3, N=8, J=9, all 1-DOF joints. Confirm dof = 3 with `grubler`.",
 "def grubler(m, N, J, fs):\n    pass\n",grubler,
 "def grubler(m, N, J, fs):\n    return m * (N - 1 - J) + sum(fs)\n",
 [[3,8,9,[1,1,1,1,1,1,1,1,1]],[3,5,6,[1,1,1,1,1,1]]])

# ---- Ch8: Dynamics ----
C('ch08','ch08-torque',"Single-Joint Inverse Dynamics",'Medium','joint_torque',['lagrangian'],
 "A pendulum joint: τ = I·θ̈ + m·g·l·sinθ. Implement `joint_torque(I, ddth, m, g, l, th)`.",
 "import math\n\ndef joint_torque(I, ddth, m, g, l, th):\n    pass\n",joint_torque,
 "import math\n\ndef joint_torque(I, ddth, m, g, l, th):\n    return I*ddth + m*g*l*math.sin(th)\n",
 [[1,0,1,9.81,1,PI/2],[0.5,2,2,9.81,0.5,0],[1,1,1,9.81,1,PI/6]])

C('ch08','ch08-ke',"Kinetic Energy ½q̇ᵀM(q)q̇",'Medium','kinetic_energy',['mass-matrix'],
 "With mass matrix M and joint velocity q̇, KE = ½ q̇ᵀ M q̇. Implement `kinetic_energy(M, v)` for n×n M and length-n v.",
 "def kinetic_energy(M, v):\n    pass\n",kinetic_energy,
 "def kinetic_energy(M, v):\n    n = len(v)\n    return 0.5*sum(v[i]*M[i][j]*v[j] for i in range(n) for j in range(n))\n",
 [[[[1,0],[0,1]],[2,0]],[[[2,1],[1,2]],[1,1]]])

C('ch08','ch08-rotke',"Rotational Kinetic Energy",'Easy','rotational_ke',['dynamics'],
 "Spinning body: KE = ½ I ω². Implement `rotational_ke(I, w)`.",
 "def rotational_ke(I, w):\n    pass\n",rotational_ke,
 "def rotational_ke(I, w):\n    return 0.5*I*w*w\n",
 [[2,3],[1,0],[0.5,4]])

# ---- Ch9: Trajectory Generation ----
C('ch09','ch09-cubic',"Cubic Time Scaling",'Easy','cubic',['time-scaling'],
 "s(t) = 3(t/Tf)² − 2(t/Tf)³, s∈[0,1]. Implement `cubic(Tf, t)`.",
 "def cubic(Tf, t):\n    pass\n",cubic,
 "def cubic(Tf, t):\n    a = t/Tf\n    return 3*a**2 - 2*a**3\n",
 [[2,0],[2,1],[2,2],[5,2.5]])

C('ch09','ch09-cubicdot',"Cubic Scaling Velocity ṡ(t)",'Medium','cubic_dot',['time-scaling'],
 "ṡ(t) = (6/Tf)·(t/Tf)·(1 − t/Tf). Implement `cubic_dot(Tf, t)`. (Peak speed is at the midpoint.)",
 "def cubic_dot(Tf, t):\n    pass\n",cubic_dot,
 "def cubic_dot(Tf, t):\n    a = t/Tf\n    return (6/Tf)*a*(1-a)\n",
 [[2,0],[2,1],[2,2],[4,2]])

C('ch09','ch09-quintic',"Quintic Time Scaling",'Medium','quintic',['time-scaling'],
 "s(t) = 10(t/Tf)³ − 15(t/Tf)⁴ + 6(t/Tf)⁵ (zero end velocity AND acceleration).\n\nImplement `quintic(Tf, t)`.",
 "def quintic(Tf, t):\n    pass\n",quintic,
 "def quintic(Tf, t):\n    a = t/Tf\n    return 10*a**3 - 15*a**4 + 6*a**5\n",
 [[2,0],[2,1],[2,2],[4,1]])

C('ch09','ch09-line',"Straight-Line Path Point",'Easy','straight_line',['path'],
 "A straight-line path: X(s) = Xstart + s·(Xend − Xstart), elementwise. Implement `straight_line(start, end, s)` for equal-length vectors.",
 "def straight_line(start, end, s):\n    pass\n",straight_line,
 "def straight_line(start, end, s):\n    return [start[i] + s*(end[i]-start[i]) for i in range(len(start))]\n",
 [[[0,0],[10,4],0.5],[[1,2,3],[3,2,1],0.0],[[0,0],[2,2],1.0]])

# ---- Ch10: Motion Planning ----
C('ch10','ch10-neighbors',"Grid Neighbors (4-connected)",'Easy','grid_neighbors',['grid'],
 "Return the valid 4-connected neighbors of cell (r,c) inside an rows×cols grid, as a **sorted** list of [r,c].\n\nImplement `grid_neighbors(r, c, rows, cols)`.",
 "def grid_neighbors(r, c, rows, cols):\n    pass\n",grid_neighbors,
 "def grid_neighbors(r, c, rows, cols):\n    out=[]\n    for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):\n        nr,nc=r+dr,c+dc\n        if 0<=nr<rows and 0<=nc<cols: out.append([nr,nc])\n    return sorted(out)\n",
 [[0,0,3,3],[1,1,3,3],[2,2,3,3]])

C('ch10','ch10-manhattan',"Manhattan Heuristic",'Easy','manhattan',['heuristic'],
 "A* on a 4-connected grid uses h = |Δr| + |Δc|. Implement `manhattan(a, b)` for cells [r,c].",
 "def manhattan(a, b):\n    pass\n",manhattan,
 "def manhattan(a, b):\n    return abs(a[0]-b[0]) + abs(a[1]-b[1])\n",
 [[[0,0],[3,4]],[[2,2],[2,2]],[[5,1],[0,9]]])

C('ch10','ch10-euclid',"Euclidean Distance",'Easy','euclidean',['heuristic'],
 "Straight-line heuristic h = √(Δr² + Δc²). Implement `euclidean(a, b)`.",
 "import math\n\ndef euclidean(a, b):\n    pass\n",euclidean,
 "import math\n\ndef euclidean(a, b):\n    return math.hypot(a[0]-b[0], a[1]-b[1])\n",
 [[[0,0],[3,4]],[[1,1],[1,1]],[[0,0],[1,1]]])

C('ch10','ch10-cheby',"Chebyshev Heuristic (8-connected)",'Easy','chebyshev',['heuristic'],
 "For an 8-connected grid, h = max(|Δr|, |Δc|). Implement `chebyshev(a, b)`.",
 "def chebyshev(a, b):\n    pass\n",chebyshev,
 "def chebyshev(a, b):\n    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))\n",
 [[[0,0],[3,4]],[[2,7],[5,5]]])

# ---- Ch11: Robot Control ----
C('ch11','ch11-pid',"PID Control Law",'Easy','pid',['feedback'],
 "u = Kp·e + Ki·∫e + Kd·ė. Implement `pid(Kp, Ki, Kd, e, edot, eint)`.",
 "def pid(Kp, Ki, Kd, e, edot, eint):\n    pass\n",pid,
 "def pid(Kp, Ki, Kd, e, edot, eint):\n    return Kp*e + Ki*eint + Kd*edot\n",
 [[2,0,0,3,0,0],[1,0.5,0.1,2,-1,4],[10,1,5,0.2,0.1,0.3]])

C('ch11','ch11-pd',"PD Set-Point Control",'Medium','pd_control',['feedback'],
 "PD law toward a desired state: u = Kp·(θd − θ) + Kd·(θ̇d − θ̇).\n\nImplement `pd_control(Kp, Kd, th, thd, th_d, thd_d)` (th_d, thd_d are desired).",
 "def pd_control(Kp, Kd, th, thd, th_d, thd_d):\n    pass\n",pd_control,
 "def pd_control(Kp, Kd, th, thd, th_d, thd_d):\n    return Kp*(th_d - th) + Kd*(thd_d - thd)\n",
 [[10,2,0,0,1,0],[5,1,1,0.5,1,0.5],[4,3,2,1,0,0]])

C('ch11','ch11-stable',"PD Stability Condition",'Easy','stable',['error-dynamics'],
 "θ̈ₑ + Kd·θ̇ₑ + Kp·θₑ = 0 is stable iff Kp>0 and Kd>0. Implement `stable(Kp, Kd)` → bool.",
 "def stable(Kp, Kd):\n    pass\n",stable,
 "def stable(Kp, Kd):\n    return Kp > 0 and Kd > 0\n",
 [[1,1],[0,1],[-2,3],[5,0]])

C('ch11','ch11-damping',"Classify Damping",'Medium','damping_type',['error-dynamics'],
 "Given damping ratio ζ, classify the second-order error response: ζ>1 'overdamped', ζ=1 'critically damped', 0<ζ<1 'underdamped'.\n\nImplement `damping_type(zeta)` returning the exact string.",
 "def damping_type(zeta):\n    pass\n",damping_type,
 "def damping_type(zeta):\n    if abs(zeta-1) < 1e-9: return 'critically damped'\n    return 'overdamped' if zeta > 1 else 'underdamped'\n",
 [[0.5],[1.0],[2.0]])

# ---- Ch12: Grasping & Manipulation ----
C('ch12','ch12-cone',"Friction Cone Half-Angle",'Easy','friction_cone_angle',['friction'],
 "α = arctan(μ). Implement `friction_cone_angle(mu)` (radians).",
 "import math\n\ndef friction_cone_angle(mu):\n    pass\n",friction_cone_angle,
 "import math\n\ndef friction_cone_angle(mu):\n    return math.atan(mu)\n",
 [[0],[1],[0.5]])

C('ch12','ch12-incone',"Inside the Friction Cone?",'Easy','in_friction_cone',['friction'],
 "No slip when |ft| ≤ μ·fn (fn ≥ 0). Implement `in_friction_cone(mu, fn, ft)` → bool.",
 "def in_friction_cone(mu, fn, ft):\n    pass\n",in_friction_cone,
 "def in_friction_cone(mu, fn, ft):\n    return abs(ft) <= mu*fn\n",
 [[0.5,10,4],[0.5,10,6],[1,2,-2],[0.3,5,2]])

C('ch12','ch12-formclosure',"Min Contacts for Form Closure",'Medium','min_contacts_form_closure',['form-closure'],
 "First-order form closure needs at least 4 frictionless point contacts in the plane, 7 in space.\n\nImplement `min_contacts_form_closure(planar)` (bool → int).",
 "def min_contacts_form_closure(planar):\n    pass\n",min_contacts_form_closure,
 "def min_contacts_form_closure(planar):\n    return 4 if planar else 7\n",
 [[True],[False]])

C('ch12','ch12-wrench',"Planar Contact Wrench",'Medium','contact_wrench',['wrench'],
 "A planar force (fx,fy) applied at point (px,py) produces wrench [m, fx, fy] with moment m = px·fy − py·fx.\n\nImplement `contact_wrench(fx, fy, px, py)`.",
 "def contact_wrench(fx, fy, px, py):\n    pass\n",contact_wrench,
 "def contact_wrench(fx, fy, px, py):\n    return [px*fy - py*fx, fx, fy]\n",
 [[1,0,0,1],[0,1,2,0],[3,4,1,1]])

# ---- Ch13: Wheeled Mobile Robots ----
C('ch13','ch13-diff',"Differential-Drive Chassis Twist",'Medium','diff_drive',['mobile'],
 "ω = r(uR−uL)/L, vx = r(uR+uL)/2, vy = 0. Implement `diff_drive(r, L, uL, uR)` → [ω, vx, vy].",
 "def diff_drive(r, L, uL, uR):\n    pass\n",diff_drive,
 "def diff_drive(r, L, uL, uR):\n    return [r*(uR-uL)/L, r*(uR+uL)/2, 0]\n",
 [[0.1,0.5,1,1],[0.1,0.5,-1,1],[0.05,0.3,2,4]])

C('ch13','ch13-wheels',"Diff-Drive Inverse: Wheel Speeds",'Medium','wheel_speeds_diff',['mobile'],
 "Invert the diff-drive map: given chassis (v, ω) find wheel speeds uL=(2v−ωL)/(2r), uR=(2v+ωL)/(2r).\n\nImplement `wheel_speeds_diff(v, w, r, L)` → [uL, uR].",
 "def wheel_speeds_diff(v, w, r, L):\n    pass\n",wheel_speeds_diff,
 "def wheel_speeds_diff(v, w, r, L):\n    return [(2*v - w*L)/(2*r), (2*v + w*L)/(2*r)]\n",
 [[1,0,0.1,0.5],[0,1,0.1,0.5],[0.5,2,0.05,0.3]])

C('ch13','ch13-unicycle',"Unicycle Odometry Step",'Medium','unicycle_step',['odometry'],
 "Integrate one step (Euler): x' = x + v·cosφ·dt, y' = y + v·sinφ·dt, φ' = φ + ω·dt.\n\nImplement `unicycle_step(x, y, phi, v, w, dt)` → [x, y, phi].",
 "import math\n\ndef unicycle_step(x, y, phi, v, w, dt):\n    pass\n",unicycle_step,
 "import math\n\ndef unicycle_step(x, y, phi, v, w, dt):\n    return [x + v*math.cos(phi)*dt,\n            y + v*math.sin(phi)*dt,\n            phi + w*dt]\n",
 [[0,0,0,1,0,1],[0,0,PI/2,2,0,0.5],[1,1,0,1,1,1]])

# ============================ emit ============================
def jnorm(x):
    if isinstance(x, bool): return x
    if isinstance(x, float): return round(x, 9)
    if isinstance(x, (list, tuple)): return [jnorm(i) for i in x]
    return x

out = {}
for chap, items in CH.items():
    arr = []
    for it in items:
        tests = [{'args': a, 'expected': jnorm(it['sol'](*a))} for a in it['args']]
        rec = {k: it[k] for k in ('id','title','difficulty','func','tags','prompt','starter')}
        rec['solution'] = it['ref']
        rec['tests'] = tests
        arr.append(rec)
    out[chap] = arr

here = os.path.dirname(os.path.abspath(__file__))
dest = os.path.join(here, '..', 'src', 'lib', 'data', 'challenges.json')
with open(dest, 'w') as f: json.dump(out, f, indent=2)
print(f"wrote {sum(len(v) for v in out.values())} challenges across {len(out)} chapters")
