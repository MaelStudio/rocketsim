import pyxel

SCREEN_W = 256
M_TO_PX = 5
FPS = 60

# APP
class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_W, title="Simulateur de Fusée Modulaire", fps=FPS)
        pyxel.load("u2.pyxres")
        pyxel.mouse(True)

        # Game
        self.rocket = Rocket(8)
        self.moon = Moon(100000*M_TO_PX)
        self.cam = Camera(114, 200)
        self.bg = Background()

        self.building = True
        self.current_module_i = 0

        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
    
        if self.building:
            if pyxel.btnp(pyxel.KEY_RIGHT):
                self.rocket.modules[self.current_module_i].type += 1
                if self.rocket.modules[self.current_module_i].type > 6:
                    self.rocket.modules[self.current_module_i].type = 0
            elif pyxel.btnp(pyxel.KEY_LEFT):
                self.rocket.modules[self.current_module_i].type -= 1
                if self.rocket.modules[self.current_module_i].type < 0:
                    self.rocket.modules[self.current_module_i].type = 6
            elif pyxel.btnp(pyxel.KEY_UP):
                self.current_module_i += 1
                if self.current_module_i > len(self.rocket.modules)-1:
                    self.current_module_i = 0
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.current_module_i -= 1
                if self.current_module_i < 0:
                    self.current_module_i = len(self.rocket.modules)-1
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.building = False
        
        if pyxel.btnp(pyxel.KEY_R):
            self.rocket = Rocket(8)
            self.building = True
            self.current_module_i = 0
            
        self.rocket.update()
        self.cam.update(self.rocket)

    def draw(self):
        pyxel.cls(1)
        self.bg.draw(self.cam.pos)
        self.rocket.draw(self.cam.pos, self.building)

        # UI
        pyxel.text(8,8, f"Altitude: {str(int(-max(self.rocket.bottom_y, self.rocket.top_y)/M_TO_PX))} M", 0)
        pyxel.text(8,16, f"Speed: {str(int(-self.rocket.vel[1]/M_TO_PX))} M/S", 0)
        pyxel.text(SCREEN_W-50,8, f"Fuel: {int((self.rocket.fuel/self.rocket.max_fuel)*100)} %", 0)

        if self.building:
            pyxel.text(8,225, "[fleche gauche/droite] pour changer le type de module", 0)
            pyxel.text(8,235, "[fleche haut/bas] pour passer au module suivant", 0)
            pyxel.text(8,245, "[espace] pour lancer la fusee", 0)

            cursor_img = (34, 162, 12, 12)
            pyxel.blt(100, 184-(self.current_module_i*self.rocket.module_spacing), 0, cursor_img[0], cursor_img[1], cursor_img[2], cursor_img[3], colkey=4, rotate=-90)
        elif self.rocket.crashed:
            pyxel.text(8,245, "[R] pour reconstruire la fusee", 0)
        else:
            pyxel.text(8,225, "[espace] pour allumer le moteur", 0)
            pyxel.text(8,235, "[fleche gauche/droite] pour diriger la fusee", 0)
            pyxel.text(8,245, "[R] pour reconstruire la fusee", 0)

        # Altitude bar
        bar_len = 140
        bar_y = 60
        cursor_img = (34, 162, 12, 12)
        moon_img = (112, 144, 16, 16)
        pyxel.rect(SCREEN_W-12, bar_y, 4, bar_len, 7)
        pyxel.blt(SCREEN_W-18, bar_y-18, 0, moon_img[0], moon_img[1], moon_img[2], moon_img[3], colkey=4)
        pyxel.blt(SCREEN_W-26, (bar_y+bar_len-6 - (-self.rocket.pos[1]/self.moon.dist)*bar_len), 0, cursor_img[0], cursor_img[1], cursor_img[2], cursor_img[3], colkey=4, rotate=-90)

# FUSEE
class Rocket:
    def __init__(self, size):
        self.module_spacing = 15
        self.modules = [Module((0, 0-i*self.module_spacing), 3) for i in range(size)]

        # Stats
        self.thrust = 200 # Newtons
        self.mass_per_module = 10 # kg
        self.max_fuel = 1000000 # Liters
        self.fuel = self.max_fuel
        self.fuel_burn_rate = 20000 # L/s
        self.speed_to_crash = 10*M_TO_PX # m/s
        
        self.gravity = 9.81*M_TO_PX # m/s^2
        
        # Rocket position
        self.vel = [0, 0]
        self.pos = [0, 0]
        self.angular_vel = 0 # deg/s
        self.angle = 90 # deg
        
        self.liftoff = False
        self.crashed = False

    def update(self):
        real_module_count = sum([int(module.type != len(module.types)-1) for module in self.modules])
        self.mass = self.mass_per_module*real_module_count # kg
        self.center_of_mass = [self.modules[0].w/2, -self.module_spacing*real_module_count/2]
        
        a = -self.angle + 90
        self.top_y = self.pos[1] + self.center_of_mass[1] + (pyxel.sin(a)*(self.modules[-1].pos_on_rocket[0]-self.center_of_mass[0]) + pyxel.cos(a)*(self.modules[-1].pos_on_rocket[1]-self.center_of_mass[1]))
        self.bottom_y = self.pos[1] + self.center_of_mass[1] + (pyxel.sin(a)*(self.modules[0].pos_on_rocket[0]-self.center_of_mass[0]) + pyxel.cos(a)*(self.modules[0].pos_on_rocket[1]-self.center_of_mass[1]))
        
        if max(self.bottom_y, self.top_y) < 0:
            # Gravity
            self.vel[1] += self.gravity/FPS
        else:
            if(self.vel[1]):
                print(self.vel[1])
            if self.liftoff and (self.vel[1] >= self.speed_to_crash):
                self.crashed = True
            self.vel[0] = 0
            self.vel[1] = 0
            self.angular_vel = 0
                
        # Burn
        if pyxel.btn(pyxel.KEY_SPACE) and self.fuel>0 and not self.crashed:
            self.fuel -= self.fuel_burn_rate/FPS
            self.vel[0] += (self.thrust * pyxel.cos(self.angle)) / (self.mass + 0.0001)
            self.vel[1] -= (self.thrust * pyxel.sin(self.angle)) / (   self.mass + 0.0001)

        # Update velocityy
        for axis in (0,1):
            self.pos[axis] += self.vel[axis]/FPS

        # Update angle
        self.angle += self.angular_vel/FPS

        # Instability
        b = pyxel.rndf(-5,5)
        for module in (self.modules):
            if module.type > 2:
                self.angular_vel += b
            else:
                if module.pos_on_rocket[1] > self.center_of_mass[1]:
                    self.angular_vel *= 0.3
                else:
                    self.angular_vel += 5*b

        # Control
        if pyxel.btn(pyxel.KEY_RIGHT) and not self.crashed:
            self.angular_vel -= 20
        if pyxel.btn(pyxel.KEY_LEFT) and not self.crashed:
            self.angular_vel += 20

        self.angular_vel *= 0.97
        
        if self.pos[1] <= -10:
            self.liftoff = True

    def draw(self, cam_pos, building):
        for module in self.modules:
            module.draw(cam_pos, self)
            
        # CG
        if building:
            pyxel.circ(self.center_of_mass[0]-cam_pos[0], self.center_of_mass[1]-cam_pos[1], 3, 7)
            pyxel.circ(self.center_of_mass[0]-cam_pos[0], self.center_of_mass[1]-cam_pos[1], 2, 0)
            pyxel.circ(self.center_of_mass[0]-cam_pos[0], self.center_of_mass[1]-cam_pos[1], 1, 7)
                    
        # draw flame
        flame_img = (64, 128, 16, 16)
        if (not building) and pyxel.btn(pyxel.KEY_SPACE) and self.fuel>0 and not self.crashed:
            a = -self.angle + 90
            x = 8+self.pos[0] + self.center_of_mass[0] +      (pyxel.cos(a)*(-self.center_of_mass[0]) - pyxel.sin(a)*(24-self.center_of_mass[1]))
            y = self.pos[1] + self.center_of_mass[1] - 24 + (pyxel.sin(a)*(-self.center_of_mass[0]) + pyxel.cos(a)*(24-self.center_of_mass[1]))
            pyxel.blt(x-cam_pos[0], y-cam_pos[1], 0, flame_img[0], flame_img[1], flame_img[2], flame_img[3], colkey=4, rotate=a+(pyxel.frame_count%4)*10-20)

# MODULE DE FUSEE
class Module:
    def __init__(self, xy, type):
        self.types = [
            (0,0),
            (32, 0),
            (64, 0),
            (0, 184),
            (32, 184),
            (64, 184),
            (200, 200)
        ]
        self.type = type
        self.pos_on_rocket = xy
        self.w, self.h = 32, 24
    
    def draw(self, cam_pos, rocket):
        if self.type == len(self.types)-1:
            return
        self.img_pos = self.types[self.type]
        a = -rocket.angle + 90
        x = rocket.pos[0] + rocket.center_of_mass[0] +      (pyxel.cos(a)*(self.pos_on_rocket[0]-rocket.center_of_mass[0]) - pyxel.sin(a)*(self.pos_on_rocket[1]-rocket.center_of_mass[1]))
        y = rocket.pos[1] + rocket.center_of_mass[1] - 24 + (pyxel.sin(a)*(self.pos_on_rocket[0]-rocket.center_of_mass[0]) + pyxel.cos(a)*(self.pos_on_rocket[1]-rocket.center_of_mass[1]))
        
        if rocket.crashed:
            flame_img = (64, 128, 16, 16)
            pyxel.blt(x+8-cam_pos[0], y+10-cam_pos[1], 0, flame_img[0], flame_img[1], flame_img[2], flame_img[3], colkey=4)
        else:
            pyxel.blt(x-cam_pos[0], y-cam_pos[1], 0, self.img_pos[0], self.img_pos[1], self.w, self.h, colkey=4, rotate=90-rocket.angle)

# MOON
class Moon:
    def __init__(self, dist):
        self.dist = dist

# CAMERA
class Camera:
    def __init__(self, offset_x, offset_y):
        self.pos = [offset_x, offset_y]
        self.offset = [offset_x, offset_y]
    
    def update(self, rocket):
        for axis in (0,1):
            target = rocket.pos[axis] - self.offset[axis]
            dist = target - self.pos[axis]
            
            self.pos[axis] += dist/2

# BACKGROND
class Background:
    def __init__(self):
        pass
    
    def draw(self, cam_pos):
        # DRAW BG
        dots_n = 6
        spacing = SCREEN_W / dots_n
        for i in range(dots_n//2 + 1):
            y1 = 2*i*spacing - (cam_pos[1]/10 % spacing*2)
            y2 = y1 + spacing
            for j in range(dots_n+1):
                x1 = j*spacing+8 - (cam_pos[0]/10 % spacing)
                x2 = x1 - spacing/2
                pyxel.circ(x1, y1+2, 1, 7)
                pyxel.circ(x2, y2+2, 1, 7)
                
        # DRAW GROUND
        pyxel.rect(0, 0 - cam_pos[1], SCREEN_W, 200, 4)
    
App()          