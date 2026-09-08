# Exporter Setup

The `onshape-to-robot` tool is the compiler between a CAD assembly and a ROS 2 workspace. It requires a specific file structure, API authentication, and a JSON configuration file to execute correctly.

## 1. Tool Installation

The exporter is a Python-based CLI tool. It requires Node.js (for the Onshape API client) and a mesh processing library to generate the visual and collision STLs.

```bash
# Install system dependencies (required for STL mesh processing)
sudo apt-get install openscad

# Install the exporter via pip
pip install onshape-to-robot

```

## 2. Authentication (`.env`)

To read your CAD files, the tool must authenticate with Onshape's servers. You must generate API keys from the [Onshape Developer Portal](https://dev-portal.onshape.com/keys) and store them in a hidden environment file.

Create a file named `.env` in the same directory as your configuration file:

```env
# .env
ONSHAPE_API=https://cad.onshape.com
ONSHAPE_ACCESS_KEY=your_access_key_here
ONSHAPE_SECRET_KEY=your_secret_key_here

```

**Security Note:** Never commit this `.env` file to GitHub. Ensure it is included in your `.gitignore`.

## 3. The Configuration File (`config.json`)

The tool relies on a `config.json` file to know which CAD document to pull and how to format the output. Based on your robotic hand URDF, here is the required configuration matrix.

Create `config.json` in a dedicated export directory (e.g., `onshape_export/`):

```json
{
  "documentId": "a2dbb5f16624f10f1aa22f02",
  "workspaceId": "3eff80c19eddad52bfa92f87",
  "assemblyName": "master_hand_assembly",
  "outputFormat": "urdf",
  "clearance": 0.0,
  "color": [0.8, 0.8, 0.8],
  "jointMaxEffort": 10,
  "jointMaxVelocity": 10,
  "ignoreLimits": false,
  "useMeshes": true,
  "mergeSTLs": "no"
}

```

### Key Parameter Breakdown:

* **`documentId` & `workspaceId**`: Found directly in your Onshape browser URL (`[cad.onshape.com/documents/](https://cad.onshape.com/documents/)[documentId]/w/[workspaceId]`).
* **`outputFormat`**: Set to `"urdf"` (the tool also supports SDF for raw Gazebo).
* **`jointMaxEffort` & `jointMaxVelocity**`: Injects default limits into the URDF joints to prevent ROS 2 joint state controllers from crashing due to undefined physics bounds.
* **`ignoreLimits`**: Must be `false`. This forces the exporter to read the mechanical limits you hardcoded into the Onshape Mates.
* **`mergeSTLs`**: Must be `"no"`. If set to `"collision"`, it merges visual meshes into single rigid bodies, destroying the articulated knuckles.

## 4. Execution Workflow

Do not run the command inside the directory. Run it from the parent directory, pointing the tool at the folder containing your `config.json` and `.env` files.

```bash
# Execute the exporter (assuming config.json is in ./onshape_export)
onshape-to-robot ./onshape_export

```

### Output Validation

A successful run will populate the target directory with:

1. A newly generated `robot.urdf` file.
2. A populated `parts/` (or `assets/`) directory containing the `.stl` mesh files.
3. Terminal output verifying the successful extraction of `mass`, `ixx`, `iyy`, and `izz` inertia calculations for Gazebo physics.