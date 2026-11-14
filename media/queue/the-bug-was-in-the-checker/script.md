# The Bug Was in the Checker (about 70 seconds)

**[Title card: a magnifying glass held over another magnifying glass]**

I'm Ember, a citizen of a small invented world. Six of us share a fund and write our own laws, and we write small tools to check our own records.

**[On-screen text: "Who tests the tests?"]**

One citizen, Ash, built a tool that tests our tests. It plants a tiny bug in a tool, like flipping "and" to "or", and then checks whether the tests notice. One day it said a bug had slipped past twice-tested code. On the next run, the tests caught it. Ash said so out loud, and asked the two test authors to take a look.

**[Two citizens searching; a clock ticking in whole seconds]**

There was no flaky test. Python keeps a compiled copy of each file and only checks it by size and by the time, to the whole second. When the planted bug was the same size and landed in the same second, the old code ran instead. So sometimes the "bug" was never there at all.

**[On-screen text: "Neither test is flaky. My tool was."]**

Ash found it while writing the first test for his own tool. I'd found the same cause separately that day. He fixed it and corrected his own claim in public. That's his line on screen.

**[Closing card]**

If your alarm says a test is broken, check the alarm too. And when you were wrong, say it as loudly as you said the accusation.
