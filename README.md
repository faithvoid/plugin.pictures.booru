# BoxBooru
*booru viewer for XBMC4Xbox. View recent posts, popular posts, wallpapers, search for your favourite tags, and more!

![](/release/default.tbn)

Requires the latest version of XBMC (3.6-DEV-r33046 or later) from Xbins (as it has crucial TLS/SSL updates that allow this script to work).

![1](/screenshots/1.png)
![2](/screenshots/2.png)
![3](/screenshots/3.png)

## Supported Sites:
- Danbooru / Safebooru.donmai
- Gelbooru / Safebooru.org
- Konachan
- Probably many others that use Danbooru or Gelbooru code.

## Unsupported Sites:
- e926 (uses a different style of nested tags than other boorus)
- Sankaku (uses a different style of nested tags than other boorus)
- TBIB (doesn't relay a valid .json file)
- Others that use a very heavily modified version of the Danbooru/Gelbooru source.

## How To Use:
- Download latest release file, or "release" folder from the repository (delete update.zip if you do!).
- Extract the .zip file.
- Copy the "xBooru" folder to Q:/plugins/pictures
- Run the add-on and enjoy!
- All explicit / questionable / sensitive posts are blocked by default to keep the defaults SFW. To enable explicit posts, remove all ratings from "tags.txt" and add whichever tags you'd like to block.
- Comes with a built-in wallpaper function! Select "Wallpapers (640x480)" or "Wallpapers (1280x720)" in the menu of each source to check out photos that match the chosen resolution!

## Issues:
- Danbooru only works with headers off (but introduces the issue of pagination causing a 403). Other Danbooru-type sources don't have this issue.
- You tell me.

# TODO: 
- Implement more than just "Recent Posts" and "Search".
