# Solr-Reddit-Utils

<!-- TOC -->
## Contents
* [Solr Setup from Scratch](#solr-setup-from-scratch)
* [Modifying the Setup](#modifying-the-setup)
  * [Changing Velocity UI (only for Solr versions under v9.0)](#changing-velocity-ui-only-for-solr-versions-under-v90)
  * [Adding fields to the database](#adding-fields-to-the-database)
* [Solr Resources](#solr-resources)
* [Reddit Fields](#reddit-fields)
  * [Submission fields](#submission-fields)
  * [Comment fields](#comment-fields)
  * [Author fields](#author-fields)
  * [Resources](#resources-1)
<!-- TOC -->

## Solr Setup from Scratch
1. Download and untar the Solr binary
   ```bash
   wget https://www.apache.org/dyn/closer.lua/solr/solr/9.3.0/solr-9.3.0.tgz?action=download
   tar -xzvf solr-9.3.0.tgz
   ```
   
2. Add Solr `bin` to `PATH`. Add the following lines to your `~/.bashrc` and then run `source ~/.bashrc` to reload the environment.
   ```bash
   export SOLR_HOME="/path/to/solr/dir"
   export PATH="${SOLR_HOME}/bin:${PATH}"
   ```

3. Modify `setup_core.sh` to your setup and load Reddit data with `setup_core.sh`

4. To access the UI, forward ports by running this on your local machine (i.e. laptop): 
   ```bash
   ssh -L 8983:localhost:8983 ${USER}@<server address>
   ```
   Open [http://localhost:8983/solr](http://localhost:8983/solr) for the Solr Admin console or http://localhost:8983/solr/CORE-NAME/browse for the Velocity search interface.
   **NOTE: Velocity is no longer built-in for v9.0+**

**Useful Solr Commands**
* Delete a collection `solr delete -c <collection name>`
* Create a collection `solr create -c <yourCollection>`
* Stop all Solr servers `solr stop -all`
* Check for running Solr servers `solr status`
* Start a Solr service on port `8983` with `5g` of RAM. `solr start -p 8983 -m 5g`

## Modifying the Setup
You **must reload the Solr core** after any modification in order for the change to take effect. 
You can easily reload the core from the Solr Admin console under the "Core Admin" tab.
The configuration files are in `conf`.

The schema is a modified version of the provided reddit schema from the 
[reddit-archive repo](https://raw.githubusercontent.com/reddit-archive/reddit/master/solr/schema4.xml). 
Also, the other configuration files are copied from the example `techproducts` collection from the Solr tutorial. 
Those files are located in `${SOLR_HOME}/server/solr/configsets/sample_techproducts_configs/conf`.

### Changing Velocity UI (only for Solr versions under v9.0)
The VelocityResponseWriter interface are controlled by files in `velocity` and configuration `solrconfig.xml`.
* Change the default search bar query fields: `solrconfig.xml` starting at line 872.
* Add a facet: `solrconfig.xml` starting at line 906
* Change the reddit result display: `velocity/post_doc.vm`
* Create a new or alternative reddit display: `velocity/results_list.vm`

### Adding fields to the database
If the new field depends on Reddit metadata, you will need to reload the Solr core and then 
reload the data with `load_reddit_into_solr.py`.

This is not necessary if you are loading keywords as in `add_keyword_mention.py`.

1. Add the field to `conf/schema.xml`. Example fields start at line 126.
2. Change the result display for the UI (see above)

Note: If the new field is from original JSON metadata, make sure it is listed in field to `reddit_object_datatypes.json`.

## Solr Resources
Note: Make sure the resources are for the specific version you are using. 

* https://raw.githubusercontent.com/reddit-archive/reddit/master/solr/schema4.xml
* https://solr.apache.org/guide/8_9/solr-tutorial.html
* https://solr.apache.org/guide/8_9/solr-jdbc-python-jython.html
* https://solr.apache.org/guide/7_3/using-python.html
* https://www.reddit.com/r/redditdev/comments/2f2dj9/how_to_construct_the_permalink_for_a_comment/
* https://stackoverflow.com/questions/3452665/how-do-i-return-only-a-truncated-portion-of-a-field-in-solr
* https://solr.apache.org/guide/8_9/highlighting.html
* https://docs.bitnami.com/ibm/infrastructure/solr/get-started/access-console/

## Reddit Fields
### Submission fields
 * archived
     * Boolean
     * Whether the post is archived. This happens automatically after (?) days
 * author
     * String
     * Username of the submitter
 * Author_flair_text
     * String, null
     * Subreddit-specific “flair” or decoration that appears next to their name when they post. Null when the user does not have flair.
 * Author_flair_type
     * String
     * Usually “text” or null
 * author_fullname
     * String
     * User id prefixed with “t2_”, which indicates the id belongs to an account. This field does not appear to be useful.
 * Category
     * null
 * comment_limit
     * Integer
     * Max number of comments allowed on a post. Default appears to be 2048.
 * Content_categories
     * null
 * created_utc
     * Integer
     * Timestamp of post creation in seconds since Unix epoch
 * crosspost_parent
     * String, null
     * Name of subreddit origin for the post. “Null” if post is not a crosspost.
 * Domain
     * String
     * URL domain of shared content. For example, “self.&lt;subreddit>” for crossposts and original content and “bbc.com” for a shared news article from BBC
 * Discussion_type
     * Null
     * Appears to be related to the type of post. Either the default post or a live-chat post that can be created by a mod. [How to create a new thread of the new discussion_type "chat" : redditdev](https://www.reddit.com/r/redditdev/comments/cz7f79/how_to_create_a_new_thread_of_the_new_discussion/) 
 * Distinguished
     * Null
     * Whether the post was created by a mod? I think this is obsolete. [What does "distinguishing" do and why does it replace stickying? : help](https://www.reddit.com/r/help/comments/1x4lnd/what_does_distinguishing_do_and_why_does_it/) 
 * downs
     * Integer
     * Useless. Always 0. In order to find the number of downs you have to do (ups / upvote_ratio)
 * Full_link
     * String
     * Appears to be phased out. See URL.
 * Gilded
     * Integer
     * Number of (Reddit gold) awards for the post
 * id
     * String
     * Unique post ID
 * Is_meta
     * Boolean
     * Whether the post is about the subreddit. Marked by “[META]” tag. [What is meta? : answers](https://www.reddit.com/r/answers/comments/1eto12/what_is_meta/) 
 * Is_original_content
     * Boolean
     * Seems to be based on an “[OC]” tag. Aka useless because not all subreddits use this. Maybe when looking at r/EarthPorn or art-based communities. For text analysis use is_self instead.
 * Is_reddit_media_domain
     * Boolean
     * Whether shared content is hosted on Reddit.
 * Is_self
     * Boolean
     * Whether the post is “original”. Not a crosspost and not shared media. Regular text post.
 * Is_video
     * boolean
 * Link_flair_text
     * String, null
     * Subreddit-specific post flair. 
 * Link_flair_type
     * String
     * “text”
 * locked
     * Boolean
     * Whether the post is “locked” aka not accepting comments. Different than archiving because this is not automatic and is done by the moderators.
 * Media
     * null
 * Num_comments
     * Integer
     * Number of comments for the post. I ~think~ it includes deleted/removed comments.
 * Num_crossposts
     * Integer
     * Number of time the post has been shared in other subreddits
 * Num_duplicates
     * integer
 * Num_reports
     * Integer / null
     * Useless, always null
 * Over_18
     * Boolean
     * Whether the post is marked NSFW
 * Permalink
     * String
     * URL starting with “/r/”. Not the full URL like url and full_link.
 * Score
     * Integer
     * Total ups - total downs. Same as ups field.
 * Selftext
     * String
     * Body of the post. Contains markdown/HTML.
 * Subreddit
     * String
     * Name of subreddit
 * Subreddit_id
     * String
     * Unique ID of the subreddit. Prefixed with “t5_”
 * Thumbnail
     * String,
     * Values are “Default”, “spoiler”. I think the purpose is to hide “spoiler” posts and not display them to the scrolling user.
 * Title
     * String
     * Title of the post
 * Url
     * String
     * When the post is “original” this is the full link to the post. But when there is shared media (YouTube video, image) then it is the URL of the media
 * Ups
     * Integer
     * Number of upvotes
 * Upvote_ratio
     * Float
     * Number of upvotes / number total votes. Can be used to find the # of downvotes.

### Comment Fields
 * author
     * string
     * author username
 * author_flair_text
     * string
     * text of poster flair. Can be None.
 * author_flair_type
     * string
     * indicates type of flair. Values I’m seeing include “richtext”, “text”, and “None”
 * author_fullname
     * string
     * account identifier
 * body
     * string
     * text of the posted comment
 * collapsed
     * boolean
     * whether the comment thread is automatically collapsed
 * collapsed_reason
     * string
     * reason given for collapsing comment thread, e.g. “comment score below threshold”. Value is None if collapsed == False
 * controversiality
     * int
     * apparently whether or not a comment is controversial,[ according to this](https://deepai.org/publication/the-pushshift-reddit-dataset)
 * created_utc
     * int
     * integer timestamp marking when comment was made
 * downs
     * int
     * appears to be downvotes, but it’s always 0
 * edited
     * int
     * 0 if the comment has never been edited
         * otherwise it is the integer timestamp of the last edit
 * gildings
     * dict
     * number of Reddit silver, gold and/or platinum awards given. Stored in a dict where gid_1 is silver, gid_2 is gold, and gid_3 is platinum
 * id
     * string
     * unique identifier for the comment. used for linking.
 * is_submitter
     * boolean
     * whether commenter is the poster of the original submission
 * link_id
     * text
     * unique identifier in the format “t3_” + unique ID of original submission
 * locked
     * boolean
     * whether a comment thread is locked (whether comments can be added to it)
 * parent_id
     * text
     * unique ID of either the original submission or the comment a given comment is in reply to
 * permalink
     * text
     * full permanent link to a comment
 * stickied
     * boolean
     * whether or not a comment is “stickied” to appear at the top of all other comments
 * subreddit
     * text
     * subreddit name
 * subreddit_id
     * text
     * unique subreddit identifier
 * score
     * int
     * upvotes minus downvotes
 * score_hidden
     * bool
     * whether or not comment scores are hidden
 * total_awards_received
     * int
     * total number of awards received (includes Reddit silver/gold/premium as well as all others)
 * ups
     * int
     * upvotes minus downvotes. identical to ups

### Author fields


### Resources
* [New parameter in comment and submission objects -- "gildings" : redditdev](https://www.reddit.com/r/redditdev/comments/9ipema/new_parameter_in_comment_and_submission_objects/)
* [reddit.com: api documentation](https://www.reddit.com/dev/api)
* [pushshift/api: Pushshift API](https://github.com/pushshift/api)
* [PRAW: is there a way to get an objects fullname/type? t1_,t2_, etc. : redditdev](https://www.reddit.com/r/redditdev/comments/atrt4i/praw_is_there_a_way_to_get_an_objects/)
* [When does deleting a comment make it disappear entirely, when does deleting a comment make only the author attribution of the comment say "deleted"? : help](https://www.reddit.com/r/help/comments/361h0b/when_does_deleting_a_comment_make_it_disappear/)
