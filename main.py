import sys
import random
from snek.environment import Snek

if '--novid' in sys.argv:
    import os
    os.environ["SDL_VIDEODRIVER"] = "dummy"

def main():
    env = Snek()

    if '--test' not in sys.argv:
        states = env.reset()

        while True:
            states, _, done, _ = env.step(random.randint(0, 4))

            env.render() # Comment out this call to train faster

            if done:
                states = env.reset()

if __name__ == '__main__':
    main()
