import pygame
import sys

pygame.init()
pygame.joystick.init()

joystick_count = pygame.joystick.get_count()

if joystick_count == 0:
    print("No joysticks detected.")
    sys.exit()

print(f"{joystick_count} joystick(s) detected.\n")

# Initialize all joysticks
joysticks = []
for i in range(joystick_count):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    joysticks.append(joystick)

    print(f"Joystick {i}: {joystick.get_name()}")
    print(f"  Axes: {joystick.get_numaxes()}")
    print(f"  Buttons: {joystick.get_numbuttons()}")
    print(f"  Hats: {joystick.get_numhats()}\n")

print("Move axes or press buttons to see mappings...\n")

screen = pygame.display.set_mode((800, 700))
pygame.display.set_caption("Multi-Joystick Tester")
font = pygame.font.SysFont(None, 24)
clock = pygame.time.Clock()

def draw_text(text, x, y):
    img = font.render(text, True, (255, 255, 255))
    screen.blit(img, (x, y))

running = True
while running:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.JOYBUTTONDOWN:
            print(f"[Joystick {event.joy}] Button {event.button} pressed")

        elif event.type == pygame.JOYBUTTONUP:
            print(f"[Joystick {event.joy}] Button {event.button} released")

        elif event.type == pygame.JOYAXISMOTION:
            print(f"[Joystick {event.joy}] Axis {event.axis} value: {event.value:.3f}")

        elif event.type == pygame.JOYHATMOTION:
            print(f"[Joystick {event.joy}] Hat {event.hat} value: {event.value}")

    # Draw joystick data side-by-side
    for j_index, joystick in enumerate(joysticks):
        x_offset = 20 + j_index * 380
        y = 20

        draw_text(f"Joystick {j_index}: {joystick.get_name()}", x_offset, y)
        y += 30

        draw_text("Axes:", x_offset, y)
        y += 25
        for i in range(joystick.get_numaxes()):
            draw_text(f"Axis {i}: {joystick.get_axis(i): .3f}", x_offset, y)
            y += 20

        y += 10
        draw_text("Buttons:", x_offset, y)
        y += 25
        for i in range(joystick.get_numbuttons()):
            draw_text(f"Button {i}: {joystick.get_button(i)}", x_offset, y)
            y += 20

        y += 10
        draw_text("Hats:", x_offset, y)
        y += 25
        for i in range(joystick.get_numhats()):
            draw_text(f"Hat {i}: {joystick.get_hat(i)}", x_offset, y)
            y += 20

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
