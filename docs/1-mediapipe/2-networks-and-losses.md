# Inside the Networks

A layer deeper than [the pipeline overview](1-two-stage-pipeline.md): the architectural choices and
loss functions that let two neural networks run on a laptop CPU at video rate. You do not need this
to use MediaPipe. You need it to reason about why it behaves the way it does at the edges.

BlazePalm is a Single Shot MultiBox Detector (SSD) heavily optimized for CPU/mobile inference, relying fundamentally on **Depthwise Separable Convolutions** rather than standard convolutions.

* **Convolutional Architecture:** To bypass the massive compute cost of standard 3D convolutions, BlazePalm splits the operation into two stages: a spatial $3 \times 3$ convolution performed independently over every input channel, followed immediately by a $1 \times 1$ pointwise convolution to linearly combine those channels. This drops the computational complexity factor significantly, allowing real-time high-resolution scanning. It utilizes a Feature Pyramid Network (FPN) to extract multi-scale features across different tensor resolutions, enabling the detection of hands whether they occupy $10\%$ or $100\%$ of the image frame.
* **Bounding Box Regression Loss:** To predict the geometry of the palm crop (center $x, y$, width, height, and rotation angle), the network uses **Smooth L1 Loss**. This behaves like an L2 (squared) loss for small errors but linearly for large errors, preventing exploding gradients when the initial bounding box guesses are wildly inaccurate.
* **Classification Loss (Focal Loss):** In a standard webcam frame, there are thousands of generated anchor boxes, but only one or two contain a palm. Standard Cross-Entropy loss would be overwhelmed by the sheer volume of "easy negatives" (background). To solve this, BlazePalm uses **Focal Loss**:

$$FL(p_t) = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$



The modulating factor $(1 - p_t)^\gamma$ dynamically scales the loss based on confidence. If the network is highly confident a box is just background, the loss drops to near zero. This forces the optimizer to spend its gradient updates entirely on hard, ambiguous features (like distinguishing a hand from an arm or face).

The Hand Landmark Regressor ignores the full image and takes only the oriented $256 \times 256$ cropped tensor from BlazePalm. It processes this through a unified encoder before splitting into multiple task-specific prediction heads.

* **Convolutional Architecture:** The regressor backbone is heavily inspired by MobileNetV2, utilizing **Inverted Residuals and Linear Bottlenecks**. It aggressively downsamples the $256 \times 256$ RGB crop through strided depthwise separable convolutions into a dense, high-dimensional feature map (the encoder).
* **Multi-Task Prediction Heads & Losses:**
1. **2D Landmark Head ($x, y$):** Predicts the 21 planar coordinates. This head is trained on massive datasets of manually annotated real-world images using **Mean Squared Error (MSE)**.
2. **3D Depth Head ($z$):** Because real-world 2D datasets lack physical depth data, this specific prediction head is trained almost entirely on synthetic 3D hand datasets (where the exact physical geometry is known). The objective is an **L2 Loss** calculated as the relative distance of each joint from the wrist root $(0,0,0)$. The network learns to infer this $z$-depth from the shading, occlusion, and relative 2D spread of the fingers in the RGB crop.
3. **Presence & Handedness Heads:** Two parallel binary classification heads determine if the hand is actually in the crop (Presence) and if it is a Left or Right hand (Handedness). Both are optimized using standard **Binary Cross-Entropy (BCE) Loss**. The Presence BCE loss is the direct trigger for your temporal tracking loop; if confidence drops below the 0.5 threshold, the pipeline kills the regressor and wakes BlazePalm back up.