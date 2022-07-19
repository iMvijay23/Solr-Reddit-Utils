# Solr-Reddit-Utils

## Solr Setup from Scratch
1. Download and untar the Solr binary
   ```bash
   wget https://dlcdn.apache.org/lucene/solr/8.9.0/solr-8.9.0.tgz
   tar -xzvf solr-8.9.0.tgz
   ```
   
2. Add Solr `bin` to `PATH`. Add the following line to your `~/.bashrc` and then run `source ~/.bashrc`
   ```bash
   export PATH="/path/to/solr-8.9.0/bin:${PATH}"
   ```

3. Modify `setup_core.sh` to your setup and load Reddit data with `setup_core.sh`

4. To access the UI, forward ports by running this on your local machine (i.e. laptop): 
   ```bash
   ssh -L 8983:localhost:8983 ${USER}@<server address>
   ```
   Open [http://localhost:8983/solr](http://localhost:8983/solr) for the Solr Admin console or http://localhost:8983/solr/CORE-NAME/browse for the Velocity search interface.

**Useful Solr Commands**
* `solr delete -c <collection name>`
* `solr create -c <yourCollection>`
* `solr stop -all`
* `solr status`
* `solr start -p 8983 -m 5g`

## Modifying the Setup
You **must reload the Solr core** after any modification in order for the change to take effect. 
You can easily reload the core from the Solr Admin console under the "Core Admin" tab.
The configuration files are in `conf`.

The schema is a modified version of the provided reddit schema from the 
[reddit-archive repo](https://raw.githubusercontent.com/reddit-archive/reddit/master/solr/schema4.xml). 
Also, the other configuration files are copied from the example `techproducts` collection from the Solr tutorial. 
Those files are located in `solr-8.9.0/server/solr/configsets/sample_techproducts_configs/conf`.

### Changing Velocity UI
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

## Resources
* https://raw.githubusercontent.com/reddit-archive/reddit/master/solr/schema4.xml
* https://solr.apache.org/guide/8_9/solr-tutorial.html
* https://solr.apache.org/guide/8_9/solr-jdbc-python-jython.html
* https://solr.apache.org/guide/7_3/using-python.html
* https://www.reddit.com/r/redditdev/comments/2f2dj9/how_to_construct_the_permalink_for_a_comment/
* https://stackoverflow.com/questions/3452665/how-do-i-return-only-a-truncated-portion-of-a-field-in-solr
* https://solr.apache.org/guide/8_9/highlighting.html
* https://docs.bitnami.com/ibm/infrastructure/solr/get-started/access-console/

