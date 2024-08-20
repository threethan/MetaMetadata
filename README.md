# Quest App Metadata
Contains metadata for all Meta Quest Store and SideQuest apps.

Includes names, banners, and icons which may be useful to app launchers.

Updated daily.

*Special thanks [Ellie](https://github.com/basti564/) for the original icon scraper*

## Data Formats
- `data/oculus` contains raw data for all Meta Quest Store apps in their proprietary format
- `data/sidequest` contains raw data for all SideQuest apps in their proprietary format, *including sidequest listings for Meta Quest Store apps*
- `data/common` contains basic data for all apps in a **common format**

## Common Format
- `name` : Display name for the app
- `version`**\***: Android version string for the latest version
- `versioncode` : Android version integer for the latest version
- `landscape` : URL to the app's banner image *(2560x1440)*
- `portrait`**\***: URL to the app's portrait box-art style image *(1008x1440)*
- `square`**\***: URL to the app's detailed square image *(1440x1440)*
- `icon`**\***: URL to the app's icon image *(512x512)*
- `hero` : URL to the app's store header image *(3000x900)*
- `logo`**\***: Transclucent app logo *(Size Varies)*

**\*** *= Only available for Meta Quest Store apps*

> [!NOTE]
> Images from SideQuest may have any resolution or ratio,
> given dimensions are for Meta Quest Store apps only.

### Example Meta Quest Store App
```json
{
    "name": "Beat Saber",
    "version": "1.37.2_10091729318",
    "versioncode": 1328,
    "landscape": "https://scontent.oculuscdn.com/v/t64.5771-25/38982677_1552836461526434_1686491824434184192_n.png?_nc_cat=101&ccb=1-7&_nc_sid=6e7a0a&_nc_ohc=wJTiTD6WmgEQ7kNvgFgBqeJ&_nc_ht=scontent.oculuscdn.com&oh=00_AYCPL6avVwtZRtVvwqbMnTD7GWN3VufagYh0qR9faYJm1Q&oe=66C8B255",
    "portrait": "https://scontent.oculuscdn.com/v/t64.5771-25/39001686_1711289145640531_2450973948465119232_n.png?_nc_cat=104&ccb=1-7&_nc_sid=6e7a0a&_nc_ohc=Owbds6rMg8sQ7kNvgGMcNgJ&_nc_ht=scontent.oculuscdn.com&oh=00_AYCcfIEzsy-EnkGxDFBEnheTzY5Q-oCeblZL8CN8imnr1Q&oe=66C8B3E3",
    "square": "https://scontent.oculuscdn.com/v/t64.5771-25/39001725_2341822516096908_5137493369550798848_n.png?_nc_cat=108&ccb=1-7&_nc_sid=6e7a0a&_nc_ohc=32LlLwFuxSwQ7kNvgEmLoWz&_nc_ht=scontent.oculuscdn.com&oh=00_AYCbaxO8ba2a2Q7gwTPkGE9DE_X50qeDB_nJ6QlGRvg7Ag&oe=66C8CF68",
    "hero": "https://scontent.oculuscdn.com/v/t64.5771-25/38974474_825152174497703_4470232644923162624_n.png?_nc_cat=106&ccb=1-7&_nc_sid=6e7a0a&_nc_ohc=HvoaL2g6l8AQ7kNvgFUZyse&_nc_ht=scontent.oculuscdn.com&oh=00_AYD5QmZsiQ1U3AmVG4iQZ2-FFyThLz02al8Tj45gEbs6yA&oe=66C8BA0C",
    "icon": "https://scontent.oculuscdn.com/v/t64.5771-25/39031348_2340770506151716_7915197188303486976_n.png?_nc_cat=103&ccb=1-7&_nc_sid=6e7a0a&_nc_ohc=3DcgUJaUO80Q7kNvgHIRhl2&_nc_ht=scontent.oculuscdn.com&oh=00_AYAS_Bm8oBm2UBvWq23QQCVc1ZBRgNnHZsw58KEzk86JuQ&oe=66C8A8A3"
}
```
### Example SideQuest App
```json
{
    "name": "QuestCraft",
    "versioncode": 60178867,
    "landscape": "https://cdn.sidequestvr.com/file/304642/qcvc.png",
    "hero": "https://cdn.sidequestvr.com/file/186161/minecraft_natural_scenery_hd_minecraft-1920x1080.jpg"
}
```