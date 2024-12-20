# Have you no shame?

You have to appreciate in a library that aims to stand in judgment of software packages, and is itself a steaming pile of code-shit. That library is `Neckbeard`. Never has there been such a perfect example of throwing stones from a glass house.

The core code is tiny, weighing in at less than a meg. Even fully loaded with dependencies, Neckbeard manages to stay under 100M which is plenty reasonable - the library is at least making the effort to appear lean on the imports. The stack trace depths are respectable at first glance and complexity shows better than it should, at least on paper.

However, this illusion falls away when you actually look at the code; where a Python package should be, a jumble of single-level scripts and half-baked modules are instead poured into an overstuffed source directory. The architecture of `Neckbeard` is a spattering of classes, nested methods and modules piled high with disorganized functions. Naming is more random and scattershot than pronouns at a barista convention. It isn’t clear how much of this code was written by o1 vs sonnet, but it is clear that a human with even rudimentary programming chops had very little to do with the bulk of this masterpiece.

Test coverage is easy - there is none. Not one test, even on the code that tests the test coverage of other software’s tests. Because why bother to write tests if you can’t even be bothered to write the code in the first place?

 In short, `Neckbeard` can be described in two words:
![fucking embarrassing](https://64.media.tumblr.com/201c6288dc3788843dfa1fd6cfc27abb/f8056965cca18133-f3/s500x750/3153bd976089a7daedef649dfc07728d8cae4a7e.gifv)
