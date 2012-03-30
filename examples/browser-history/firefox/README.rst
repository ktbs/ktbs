===========================================
Populate the kTBS with your firefox history
===========================================

The following code uses the kTBS python client to populate the kTBS with your firefox navigation history.

Copy your history database, which in a file named **places.sqlite** located in your firefox profile folder to the current folder.

Then execute the following command to extract 1000 items of your history.

    $ python browser_history_to_ktbs.py -l 1000

The model and obsels have to be developped.
