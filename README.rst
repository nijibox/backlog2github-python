Porting Backlog issues to YAML
==============================

(Implemented by python)

Usage
-----

.. code-block::

   $ git clone https://github.com/nijibox/backlog2x.git
   $ cd ./backlog2x
   $ cp example.ini app.ini
   $ vi app.ini
   (Change your Space ID and API Key)
   $ ./backlog2x PROJ
   (Print issues in PROJ)
   $ ./backlog2x PROJ-1
   (Dump detail, comments and attachments from issue PROJ-1)
   $ ./backlog2x PROJ
   (Try to dump detail, comments and attachments from all issues in PROJ)
