# From Vectors to Mechanical Limits

The full kinematic chain in five steps: landmarks in, `JointState` out. This is the summary view;
[the mapping table](3-the-mapping-table.md) covers the implementation line by line.

**Vector Geometry & Triplet Math**
The pipeline begins by extracting 3D normalized coordinates $(x, y, z)$ for all 21 hand landmarks from MediaPipe. To calculate an anatomical joint angle, the code groups landmarks into sets of three: a proximal point ($p_1$), the joint pivot point itself ($p_2$), and a distal point ($p_3$). It constructs two directional vectors radiating outward from the joint pivot:


$$v_1 = p_1 - p_2 \quad \text{and} \quad v_2 = p_3 - p_2$$


These vectors represent the physical bones meeting at that specific hinge.

**The Dot Product Angle Calculation**
To find the angle between $v_1$ and $v_2$, the code applies the geometric dot product definition:


$$\cos(\theta) = \frac{v_1 \cdot v_2}{\Vert{}v_1\Vert{} \Vert{}v_2\Vert{}}$$


`np.dot(v1, v2)` computes the scalar product, divided by the product of their Euclidean lengths (`np.linalg.norm`). `np.clip` ensures floating-point inaccuracies never push the ratio outside $[-1.0, 1.0]$ (which would crash `np.arccos`). The resulting value is the raw joint angle in radians, outputting roughly $3.10$ radians for an open hand and down to $1.60$ radians for a fully bent finger.

**Normalization & Flexion Scaling**
Raw MediaPipe angles are biometric measurements from a camera, but the CAD-generated Onshape model has strict mechanical limits. To bridge this gap, the raw angle is converted into a normalized **flexion ratio** between $0.0$ (completely straight/open) and $1.0$ (completely curled/closed):


$$\text{flexion} = \frac{\text{RAW\_STRAIGHT} - \text{raw\_angle}}{\text{RAW\_STRAIGHT} - \text{RAW\_CURLED}}$$


`np.clip(flexion, 0.0, 1.0)` prevents tracking jitter or over-extension from breaking the calculation when your fingers stretch past normal boundaries.

**URDF Linear Interpolation**
Once the normalized flexion factor is known, it is mapped directly onto your URDF’s explicit joint limits using linear interpolation (lerp):


$$\text{urdf\_angle} = \text{open\_angle} + \text{flexion} \times (\text{closed\_angle} - \text{open\_angle})$$


This step translates a human hand gesture into the exact mechanical radian range defined in the Onshape CAD assembly (e.g., mapping `thumb_mcp` from $-1.377$ to $0.194$ radians).

**ROS 2 State Packaging**
The final translated values are loaded into arrays alongside their corresponding joint names (`thumb_mcp`, `index_pip`, etc.) and wrapped into a standard `sensor_msgs/msg/JointState` message. When published to `/joint_states`, RViz reads the array names and positions, matches them to the named joints inside your URDF tree, and rotates the 3D meshes in real-time.