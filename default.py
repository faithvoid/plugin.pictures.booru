import xbmc
import xbmcgui
import xbmcplugin
import json
import urllib2  # Python 2.7 uses urllib2 instead of urllib.request
import sys
import urlparse
import urllib
import re

HANDLE = int(sys.argv[1])

# Sources configuration (name, URL, query parameters, etc.)
SOURCES = [
    {
        "name": "Safebooru",
        "base_url": "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&",
        "preview_key": "preview_url",
        "file_key": "file_url",
        "tags_key": "tags",
	"query_style": "Gelbooru",
        "use_custom_headers": True  # Enable headers for this source
    }
]

# Function to load blocked tags from a "tags.txt" file
def load_blocked_tags():
    blocked_tags = []
    try:
        with open('Q:/plugins/pictures/xBooru/tags.txt', 'r') as file:
            # Read all lines, strip newlines, and spaces
            blocked_tags = [line.strip().lower() for line in file.readlines() if line.strip()]
        xbmc.log("Loaded Blocked Tags: {0}".format(blocked_tags), xbmc.LOGINFO)
    except IOError:
        xbmc.log("tags.txt not found, no tags will be blocked.", xbmc.LOGINFO)
    return blocked_tags

# Function to get images from the selected source based on query parameters
def get_images_from_source(source, query_params=''):
    # Check if the source is Gelbooru, which has its query string embedded in the base URL
    if source["query_style"] == "Gelbooru":
        # Gelbooru-style sources embed query parameters directly
        url = "{0}{1}".format(source["base_url"], query_params)
    else:
        # Danbooru and other sources use query params appended to the base URL
        url = "{0}?{1}".format(source["base_url"], query_params)

    # Default headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
        'Accept': 'application/json'
    }

    # Check if custom headers are enabled for this source
    if source.get("use_custom_headers", False):
        xbmc.log("Using custom headers for: {}".format(source["name"]), xbmc.LOGINFO)
    else:
        xbmc.log("Using default headers for: {}".format(source["name"]), xbmc.LOGINFO)
        headers = {}

    try:
        request = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(request)
        response_data = response.read()
        json_data = json.loads(response_data)

        # Handle Gelbooru-style sources with nested structures
        if source["query_style"] == "Gelbooru":
            if isinstance(json_data, list):
                return json_data
            elif isinstance(json_data, dict) and 'post' in json_data:
                return json_data['post']
            else:
                xbmc.log('Error: Gelbooru response structure is unexpected', xbmc.LOGERROR)
                return []
        else:
            # Handle Danbooru and similar sources with flat structures
            if isinstance(json_data, list):
                return json_data
            elif isinstance(json_data, dict):
                if 'post' in json_data:
                    return [json_data['post']]
                elif 'posts' in json_data:
                    return json_data['posts']
                else:
                    xbmc.log('Error: Response does not contain "post" or "posts" key', xbmc.LOGERROR)
                    return []
            else:
                xbmc.log('Error: Source response is not a list or a dict: {}'.format(json_data), xbmc.LOGERROR)
                return []
    except Exception as e:
        xbmc.log('Error fetching source data: {0}'.format(str(e)), xbmc.LOGERROR)
        return []

def is_post_blocked(post, blocked_tags, tags_key):
    # Get the tags from the post using the specified key
    if isinstance(post, dict):
        post_tags = post.get(tags_key, [])
    elif isinstance(post, list):
        post_tags = post[0].get(tags_key, []) if post else []
    else:
        post_tags = []

    # If the tags are in a string format (common for Danbooru-style), split by spaces
    if isinstance(post_tags, str):
        post_tags = post_tags.split()
    # If the tags are in a dictionary format (common for Gelbooru-style), extract keys (tag names)
    elif isinstance(post_tags, dict):
        post_tags = list(post_tags.keys())  # Extract only the tag names (keys)
    
    # If the tags are in a list, ensure all tags are lowercase for comparison
    if isinstance(post_tags, list):
        post_tags = [tag.lower() for tag in post_tags]  # Apply lower() to each tag
    
    # Log the tags for debugging
    xbmc.log("Post Tags: {0}".format(post_tags), xbmc.LOGDEBUG)
    xbmc.log("Blocked Tags: {0}".format(blocked_tags), xbmc.LOGDEBUG)

    # Check if any tag in post matches any blocked tag
    for blocked_tag in blocked_tags:
        if blocked_tag in post_tags:
            xbmc.log("Blocking post with tags: {0} due to blocked tag: {1}".format(post_tags, blocked_tag), xbmc.LOGINFO)
            return True  # Post is blocked
    return False  # Post is not blocked




# Function to add directory items (links) to the XBMC list
def add_directory_item(url, title, is_folder=False, thumbnail=''):
    li = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)

    # Set the item to be playable (for images)
    li.setProperty("IsPlayable", "true")
    li.setPath(url)  # Set the URL to be the image URL

    # Add context menu to allow saving the image
    li.addContextMenuItems([('Save Image', 'RunPlugin(plugin://pictures/xBooru/?action=save&url={1})'.format(sys.argv[0], url))])

    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=is_folder)

# Function to create a query string based on the source's style
def create_query_string(source, tags='', page=1, limit=20):
    if source["query_style"] == "Danbooru":
        # Danbooru-style API query string construction
        query_params = {
            'tags': tags,
            'page': page,
            'limit': limit,
            'json': 1  # Ensure JSON response for Danbooru-style sources
        }
        query_string = urllib.urlencode(query_params)
        return query_string
    
    elif source["query_style"] == "Gelbooru":
        # Gelbooru-style API query string construction
        query_params = {
            'page': 'dapi',  # Fixed page for Gelbooru-style sources
            's': 'post',     # Post search
            'q': 'index',    # Query index
            'tags': tags,    # Tags to search for
            'pid': page - 1, # Gelbooru uses 0-based pagination
            'limit': limit,  # Limit for results per page
            'json': 1         # Ensure JSON response for Gelbooru-style sources
        }
        query_string = urllib.urlencode(query_params)
        return query_string
    
    else:
        # Return an empty string if source query style is not recognized
        return ''


# Function to handle the search functionality


# Function to handle the search functionality
def search_posts(source, query_tags, blocked_tags, page=1, source_id=None):
    formatted_tags = query_tags.replace(' ', '+')  # Format the tags

    # Build query string for search
    query_string = "index.php?page=dapi&s=post&q=index&tags={}&pid={}&json=1".format(
        formatted_tags, page
    )
    xbmc.log("Query String: {}".format(query_string))  # Debug

    # Fetch images using the query string
    images = get_images_from_source(source, query_string)
    
    if not images:
        xbmc.log("No images returned from the source.", xbmc.LOGERROR)
        return
    
    xbmc.log("Images returned: {}".format(images))  # Debug

    # Process each image and add to the directory
    for img in images:
        process_image(img, source, blocked_tags)

    # Add next page option with source_id to preserve the context of the search
    add_directory_item(
        "{0}?action=search&page={1}&tags={2}&source_id={3}".format(sys.argv[0], page + 1, formatted_tags, source_id), 
        "Next Page", 
        is_folder=True
    )

    xbmcplugin.endOfDirectory(HANDLE)


# Helper function to process individual images
def process_image(img, source, blocked_tags):
    # Skip the post if it's blocked
    if is_post_blocked(img, blocked_tags, source["tags_key"]):
        return

    # Use the tags of the post as the title
    tags_title = img.get(source["tags_key"], 'unknown tags').strip().replace(' ', ', ')

    # Ensure the full image URL and thumbnail are properly fetched
    image_url = img.get(source["file_key"], '')
    thumbnail_url = img.get(source["preview_key"], '')

    # Add the image item to the directory
    add_directory_item(image_url, tags_title, is_folder=False, thumbnail=thumbnail_url)




# Function to handle the user input for searching posts
def prompt_for_search_query():
    keyboard = xbmc.Keyboard('', 'Enter Search Query')
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return None  # Return None if no text is entered


# Function to display recent posts
def display_recent_posts(source, blocked_tags, page=1, source_id=None):
    # Use the correct query string for recent posts (no tags)
    query_string = create_query_string(source, tags='', page=page)
    
    # Get images
    images = get_images_from_source(source, query_string)

    for img in images:
        # Process each image (including blocked checks)
        if not is_post_blocked(img, blocked_tags, source["tags_key"]):
            process_image(img, source, blocked_tags)

    # Add next page option with source_id to preserve the context
    add_directory_item(
        "{0}?action=recent&page={1}&source_id={2}".format(sys.argv[0], page + 1, source_id),
        "Next Page", 
        is_folder=True
    )

    xbmcplugin.endOfDirectory(HANDLE)

def display_popular_posts(source, blocked_tags, page=1, source_id=None):
    # Check if the source is Gelbooru-style or Danbooru-style
    if source.get("query_style") == "Gelbooru":
        # Use 'score:>=10' for Gelbooru-style sources
        query_string = create_query_string(source, tags='score:>=10', page=page)
    elif source.get("query_style") == "Danbooru":
        # Use 'order:favcount' for Danbooru-style sources
        query_string = create_query_string(source, tags='order:score', page=page)
    else:
        # Default case if neither Gelbooru nor Danbooru is detected
        query_string = create_query_string(source, tags='', page=page)
    
    # Get images from the source using the query string
    images = get_images_from_source(source, query_string)

    # Process each image (including blocked checks)
    for img in images:
        if not is_post_blocked(img, blocked_tags, source["tags_key"]):
            process_image(img, source, blocked_tags)

    # Add next page option to allow navigation between pages
    add_directory_item(
        "{0}?action=popular&page={1}&source_id={2}".format(sys.argv[0], page + 1, source_id),
        "Next Page", 
        is_folder=True
    )

    xbmcplugin.endOfDirectory(HANDLE)



# Function to handle saving the image to disk
def save_image(image_url):
    try:
        # Ensure the URL is valid
        if not image_url:
            xbmc.log("Invalid image URL provided", xbmc.LOGERROR)
            return
        
        # Extract the filename from the URL
        file_name = image_url.split('/')[-1]
        
        # Make the filename FATX-safe
        file_name = make_fatx_safe(file_name)
        
        # Set the path to save the image
        save_path = "F:/xBooru/{}".format(file_name)  # Ensure the filename is valid

        # Log the save path for debugging
        xbmc.log("Saving image to: {0}".format(save_path), xbmc.LOGINFO)

        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0'
        }

        # Open the image URL with headers
        request = urllib2.Request(image_url, headers=headers)
        response = urllib2.urlopen(request)
        image_data = response.read()  # Read the image content

        # Save the image data to the specified path
        with open(save_path, 'wb') as image_file:
            image_file.write(image_data)  # Write the image content to the file

        # Show success message
        xbmcgui.Dialog().ok("Success!", "Image successfully saved as:", "{0}".format(file_name))

    except Exception as e:
        xbmcgui.Dialog().ok("Error!", "Error saving image: {0}".format(str(e)))

# Helper function to make the filename FATX-safe
def make_fatx_safe(file_name):
    # Remove any special characters that are not allowed in FATX file names
    # Replace with an underscore (_) or another safe character
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)  # Replace invalid chars with underscores
    
    # Truncate the filename to 255 characters (including extension)
    if len(safe_name) > 255:
        safe_name = safe_name[:255]

    # Ensure the filename doesn't have trailing spaces
    safe_name = safe_name.strip()

    return safe_name


# Function to display the source selection menu
def show_source_selection():
    xbmcplugin.setContent(HANDLE, 'folders')  # Set the content type to folders
    for idx, source in enumerate(SOURCES):
        # Add each source as a list item
        url = "{0}?action=select_source&source_id={1}".format(sys.argv[0], idx)
        add_directory_item(url, source["name"], is_folder=True)

    xbmcplugin.endOfDirectory(HANDLE)

# Main function that controls the browsing logic

def main():
    blocked_tags = load_blocked_tags()  # Load blocked tags from the "tags.txt" file

    xbmcplugin.setContent(HANDLE, 'images')
    args = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)
    action = args.get('action', [None])[0]  # Get action (if any) from URL parameters
    page = int(args.get('page', [1])[0])  # Get the page number (default to 1)
    search_tags = args.get('tags', [''])[0]  # Retrieve the search query from URL parameters

    # Handle source_id, with a check for invalid values
    source_id_str = args.get('source_id', [None])[0]
    try:
        source_id = int(source_id_str) if source_id_str is not None else -1
    except ValueError:
        xbmc.log("Invalid source_id: {}. Using default value -1.".format(source_id_str), xbmc.LOGERROR)
        source_id = -1  # Set default value in case of an invalid source_id

    if action == 'select_source':
        if source_id != -1:
            # User selected a source, proceed with search or recent posts
            selected_source = SOURCES[source_id]
            add_directory_item("{0}?action=popular&page=1&source_id={1}".format(sys.argv[0], source_id), "Popular Posts", is_folder=True)
            add_directory_item("{0}?action=recent&page=1&source_id={1}".format(sys.argv[0], source_id), "Recent Posts", is_folder=True)
            add_directory_item("{0}?action=search&page=1&source_id={1}".format(sys.argv[0], source_id), "Search Posts", is_folder=True)
            xbmcplugin.endOfDirectory(HANDLE)
        else:
            xbmc.log("No source selected. Returning to the main menu.")
            show_source_selection()

    elif action == 'search':
        if not search_tags:
            # Prompt the user to enter a search term if no tags are provided
            search_tags = prompt_for_search_query()
            if search_tags:
                # Proceed with search if valid input
                selected_source = SOURCES[source_id]
                search_posts(selected_source, search_tags, blocked_tags, page)
            else:
                xbmc.log('No search tags provided.', xbmc.LOGERROR)
            xbmcplugin.endOfDirectory(HANDLE)
        else:
            # If search_tags exist, continue with the search and pagination
            selected_source = SOURCES[source_id]
            search_posts(selected_source, search_tags, blocked_tags, page)

    elif action == 'popular':
        # Display recent posts
        selected_source = SOURCES[source_id]
        display_popular_posts(selected_source, blocked_tags, page)

    elif action == 'recent':
        # Display recent posts
        selected_source = SOURCES[source_id]
        display_recent_posts(selected_source, blocked_tags, page)


    elif action == 'save':
        # Handle saving the image
        image_url = args.get('url', [''])[0]
        save_image(image_url)

    else:
        # Main menu options: Select source
        show_source_selection()


if __name__ == '__main__':
    main()
