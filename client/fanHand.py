import math


def fanHand(n):
    """
    Return a list of transforms for a fanned hand of n cards
    """
    minPosX = 0
    maxPosX = 3
    minRot = -45.0
    maxRot = -minRot

    if n < 4:
        step = (maxPosX - minPosX) / (n + 1)
        minPosX += step
        maxPosX -= step
        rotStep = (maxRot - minRot) / (n + 1)
        minRot += rotStep
        maxRot -= rotStep

    posX = minPosX
    posY = 0.0
    rot = minRot

    transforms = []

    for i in range(0, n):
        if maxPosX - minPosX > 0:
            curve = math.sin(
                (posX - minPosX) / (maxPosX - minPosX) * math.pi)
            posZ = 0.5 * curve - 2
        else:
            posZ = -2
        transforms.append((posX, posY, posZ, 0, 0, rot))
        if n > 1:
            posX += (maxPosX - minPosX) / (n - 1)
            posY += 0.001
            rot += (maxRot - minRot) / (n - 1)

    return transforms
