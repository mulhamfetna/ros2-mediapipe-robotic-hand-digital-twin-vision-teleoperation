# From Landmarks to Joint Angles

This is the hinge of the whole project: the step where computer vision output becomes a mechanical
quantity. It runs in `compute_15_joint_angles()` in
[`hand_tracker/src/hand_tracker_node.py`](../../hand_tracker/src/hand_tracker_node.py), and it is
pure geometry — no learning, no calibration, no state.

The conversion relies on isolating three adjacent MediaPipe coordinate points to form a vertex and two vectors, then applying the geometric definition of the dot product to find the interior angle.

Here is the exact mathematical sequence executing inside your `compute_15_joint_angles` function for every frame.

### 1. Vertex Selection (The Triplets)

MediaPipe outputs a flattened list of 21 $(x, y, z)$ coordinates. To measure the flexion of a specific joint, we must isolate the coordinate of the joint itself (the vertex) and the coordinates of the two joints immediately adjacent to it.

In your code, you defined this using the `triplets` array. If we look at the Index finger's PIP joint (Landmark 6), the triplet is `(5, 6, 7)`.

* $P_1 = \text{Landmark 5 (Index MCP)}$
* $P_2 = \text{Landmark 6 (Index PIP - The Vertex)}$
* $P_3 = \text{Landmark 7 (Index DIP)}$

### 2. Vector Construction

We create two 3D vectors originating from the vertex ($P_2$) and pointing outward along the bones to $P_1$ and $P_3$.

* $\vec{v}_1 = P_1 - P_2$
* $\vec{v}_2 = P_3 - P_2$

By subtracting the vertex coordinates from the adjacent coordinates, we shift the local origin to the joint we are measuring.

### 3. The Dot Product Theorem

The algebraic dot product of two vectors is intrinsically linked to the cosine of the angle $\theta$ between them through the fundamental relation:


$$\vec{v}_1 \cdot \vec{v}_2 = \Vert{}\vec{v}_1\Vert{} \Vert{}\vec{v}_2\Vert{} \cos(\theta)$$

Where:

* $\vec{v}_1 \cdot \vec{v}_2$ is the scalar dot product: $(x_1x_2 + y_1y_2 + z_1z_2)$.
* $\Vert{}\vec{v}_1\Vert{}$ and $\Vert{}\vec{v}_2\Vert{}$ are the magnitudes (lengths) of the vectors, calculated in your code via `np.linalg.norm`.

To solve for the angle, we isolate $\cos(\theta)$:


$$\cos(\theta) = \frac{\vec{v}_1 \cdot \vec{v}_2}{\Vert{}\vec{v}_1\Vert{} \Vert{}\vec{v}_2\Vert{}}$$

### 4. Floating Point Stabilization

Before calculating the inverse cosine ($\arccos$) to find $\theta$, the algorithm must handle two critical hardware realities of computing floats in Python:

1. **Division by Zero:** If a bone length evaluates to zero (which happens if MediaPipe temporarily outputs identical coordinates for two landmarks), the division will throw a `NaN` error and crash the node. You handled this with `if norm1 < 1e-6`.
2. **Domain Errors:** The domain of $\arccos$ is strictly $[-1.0, 1.0]$. Floating-point arithmetic inaccuracies can easily result in a cosine value of `1.0000000002`. Passing this to `np.arccos` triggers a math domain exception. Your code wraps the result in `np.clip(cosang, -1.0, 1.0)` to safely clamp the boundaries.

Once stabilized, the angle is extracted:


$$\theta = \arccos(\cos(\theta))$$

### 5. The Output Space (Radians)

The $\arccos$ function returns the interior angle in radians, not degrees. This is what fixes the values of the `RAW_STRAIGHT_ANGLE` and `RAW_CURLED_ANGLE` calibration constants.

When your physical finger is completely straight, $\vec{v}_1$ and $\vec{v}_2$ point in nearly opposite directions, forming a $180^\circ$ angle.

* $180^\circ = \pi \text{ radians} \approx 3.14$
* This is why your `RAW_STRAIGHT_ANGLE` baseline is `3.10`.

When you curl your finger into a fist, the interior angle between the bones closes to approximately $90^\circ$.

* $90^\circ = \frac{\pi}{2} \text{ radians} \approx 1.57$
* This is why your `RAW_CURLED_ANGLE` baseline is `1.60`.