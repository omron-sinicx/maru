You can choose from the following two firmware versions depending on the localization method:
- `firmware-cluster-protocol.bin` : Firmware for *Pixel-level Visible Light Communication (PVLC) based method*
- `firmware-osx-protocol.bin` : Firmware for *Zooids-based method*

[Zooids-based Method] This method projects a sequence of gray-coded patterns independently. A single white image is projected, allowing the projector to be used as an illumination source. For details on this localization method and setup instructions, please refer to [Zooids documentation](https://github.com/ShapeLab/SwarmUI/tree/master/Hardware/Projector%20Tracking%20Setup).

[PVLC-based Method] This method embeds a sequence of gray-coded patterns into video content for projection. By properly configuring the data sent to the projector, visual content can be projected while maintaining localization capabilities. For detailed information on this localization method, please refer to the [paper](https://www.tandfonline.com/doi/abs/10.9746/jcmsi.11.302).

Please see `3.1.2. DFU Mode (Firmware Update)` in Hardware Manual (maru) for installation.
https://shigeodayo.notion.site/3-Basic-Usage-3bf8d7eb6677414087e91fe5fa6da7f2?pvs=25
