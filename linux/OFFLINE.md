# Optional offline image delivery node

Not the normal workflow; invoke only with explicit approval when registry delivery cannot work. Normal delivery remains fixed-digest registry pull. Requires Docker, Compose, Python3, gzip, sha256sum and sufficient disk space on Linux AMD64; this is an offline image package, not an offline Docker engine installer or offline model service.

On the packaging host, from a clean committed configuration checkout:

    python linux/offline_bundle.py pack VERIFIED_DELIVERY NEW_OUTPUT_DIRECTORY

This exports the already verified local image, not a new build. Outputs DIRECTORY.tar and DIRECTORY.tar.sha256 plus an unpacked directory. No credentials or runtime data are copied. The manifest distinguishes source/build-config/packaging-config commits, original published digest and image ID. Transfer the TAR and its checksum over authenticated SSH; compare the receiver SHA256 with the trusted sender value (a checksum alone is not a signature).

On the explicitly approved host, extract into a NEW restricted staging directory after checking the outer checksum. The generated archive contains only fixed filenames. Then run:

    sudo bash install-offline.sh

The installer verifies every payload checksum, loads the image, validates image ID/internal source identity, refuses existing deployments and occupied port 8642, and starts /opt/stevenzxs-hermes with no registry pull. A newly generated API key stays in root-only runtime.env. Never print it. API exposure remains 127.0.0.1:8642. Do not copy Windows secrets or model credentials into the bundle.

Run health/authentication checks and restart/persistence checks before acceptance. Full model access requires separate secure configuration and verification. If failure occurs, stop only this Compose project and preserve data/logs; never prune or down -v. Re-running installer refuses overwrite. Upgrades require explicit approval, old image ID/tag and consistent stopped-service data/config backup; rollback restores the matching image/config/data and repeats acceptance. Uninstall requires approval and retains data by default. See SKILL.md for further boundaries. The offline installer itself must not be treated as an upgrade tool.
