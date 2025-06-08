                   +-------------+
User (Italian) --> | Traduttore  | --> 
                   +-------------+ 
                          |
                          v
             +----------------------------+
             |  RAG (Qdrant + LLM + tools)|
             +----------------------------+
                          |
      +----------+--------+--------+-----------+
      |          |                 |           |
+-----v+    +----v-----+     +-----v-----+ +----v----+
| Web  |    | PubMed   |     | PythonREPL| | PDF Gen |
|Search|    | API      |     | Tool      | | Tool    |
+------+    +----------+     +-----------+ +---------+
                          |
                     +----v----+
                     | Traduzione|
                     +----+-----+
                          |
                     +----v----+
                     |  Output  |
                     +---------+




copiare a mano il tool per riassunti:

https://www.youtube.com/watch?v=g6Oouxm2GoE&list=LL&index=2&t=2232s
