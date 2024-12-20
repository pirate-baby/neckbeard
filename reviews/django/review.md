# An aging OSS pillar

Django was a legendary member of the fully-baked OSS web framework revolution, and we owe the library respect for that. It went beyond just software and was at the epicenter of an entire ecosystem that helped make the rapid rise of today’s internet possible.

But numbers don’t lie; like Elvis and Snoop Dog (Lion?), Django has failed to age gracefully. This is not to say the codebase is bad code, per se - more that some of the choices indicative of the time are now painful handicaps.

The elephant in the room with all batteries-included frameworks from the aughts is always size. At over a gig stock for the framework code alone, she’s a very hefty girl. Django also rarely stays stock for long; that huge plugin ecosystem means a fully built application can quickly grow to several Gigs of code, making debugging somewhere between challenging and impossible.

Test coverage is stellar, as you’d expect from an OOP poster child. Code complexity metrics are also better than average, likely from years of refactoring by very smart engineers. But the sheer girth of the codebase brings back memories of the dreaded AbstractSingletonProxyFactoryBean and all the cognitive load that comes with it.

There are also a lot of aging code security risks that, while they are not strictly exposures, are less than optimal - similar to a classic car with no seat belts in the back. It isn’t a reason not to drive it, but you’d never build one that way today.

And that classic car metaphor holds across the code base - lots of things that bring back fond memories, or are warmly familiar, but you are aware of why the new showroom machines don’t do it that way. Django has nothing to apologize for, but it may be time for it to hang up the gloves and move to Boca Raton.
