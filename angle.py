from math import sin, cos, radians

x = 0
y = 0

for i in range(4):
    x += 5*cos(radians((i+1)*(20)))
    y += 5*sin(radians((i+1)*(20)))

x += 5*cos(radians(10))
y += 5*sin(radians(10))

print(x, y, sep='\n')
