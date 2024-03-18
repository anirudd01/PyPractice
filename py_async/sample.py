# import asyncio
# counter = 1

# async def count():
#     global counter
#     counter +=1
    
#     print("One")
#     await asyncio.sleep(1)
#     print("Two")

# async def main():
#     await asyncio.gather(count(), count(), count())

# if __name__ == "__main__":
#     import time
#     s = time.perf_counter()
#     asyncio.run(main())
#     elapsed = time.perf_counter() - s
#     print(f"{__file__} executed in {elapsed:0.2f} seconds.")

# A simple generator function
def countdown(n):
    while n > 0:
        yield n
        n -= 1

# A generator function that uses `yield from`
def count_from_to(start, end):
    yield from countdown(start)
    yield from countdown(end)

# Using the generator
for x in count_from_to(3, 2):
    print(x)