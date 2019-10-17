import wx
import glob
import eyed3
import pygame
import threading

class Mp3Frame(wx.Frame):
    #main class which will start the program
    def __init__(self):
        super().__init__(parent=None, title='BeBe MP3 Player', size=(500, 300))
        self.panel = Mp3Panel(self)
        self.create_menu()
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Show()

    def onClose(self, event):
        self.panel.stop_music('event')
        self.Destroy()

    def create_menu(self):
        menu_bar = wx.MenuBar()
        #File menu setup
        file_manu = wx.Menu()
        open_folder_menu_item = file_manu.Append(
            wx.ID_ANY, 'Open Folder', 'Open a folder with MP3s')
        self.Bind(event=wx.EVT_MENU, handler=self.on_open_folder, source=open_folder_menu_item)
        open_file_menu_item = file_manu.Append(
            wx.ID_ANY, 'Open File', 'Open MP3 File')
        self.Bind(event=wx.EVT_MENU, handler=self.on_open_file, source=open_file_menu_item)
        add_folder_menu_item = file_manu.Append(
            wx.ID_ANY, 'Add Folder', 'Add a folder with MP3s')
        self.Bind(event=wx.EVT_MENU, handler=self.on_add_folder, source=add_folder_menu_item)
        add_file_menu_item = file_manu.Append(
            wx.ID_ANY, 'Add File', 'Add MP3 File')
        self.Bind(event=wx.EVT_MENU, handler=self.on_add_file, source=add_file_menu_item)
        menu_bar.Append(file_manu, '&File')
        #Edit menu setup
        edit_menu = wx.Menu()
        clear_menu_item = edit_menu.Append(
            wx.ID_ANY, 'Clear list', 'Clear the list of MP3s')
        self.Bind(event=wx.EVT_MENU, handler=self.on_clear_menu, source=clear_menu_item)
        menu_bar.Append(edit_menu, '&Edit')
        #View menu setup
        view_menu = wx.Menu()
        mp3_list_menu_hide = view_menu.Append(
            wx.ID_ANY, 'Hide track list', 'Hide the list of MP3s')
        self.Bind(event=wx.EVT_MENU, handler=self.on_hide, source=mp3_list_menu_hide)
        mp3_list_menu_show = view_menu.Append(
            wx.ID_ANY, 'Show track list', 'Show the list of MP3s')
        self.Bind(event=wx.EVT_MENU, handler=self.on_show, source=mp3_list_menu_show)

        menu_bar.Append(view_menu, '&View')
        self.SetMenuBar(menu_bar)

    #method to open get mp3 files
    def on_open_folder(self, event):
        title = 'Choose a directory'
        self._open_add(title, wx.DirDialog, 'open_folder')

    def on_open_file(self, event):
        title = 'Choose a file'
        self._open_add(title, wx.FileDialog, 'open_file')

    def on_add_folder(self, event):
        title = 'Choose a directory to add'
        self._open_add(title, wx.DirDialog, 'add_folder')

    def on_add_file(self, event):
        title = 'Choose a file to add'
        self._open_add(title, wx.FileDialog, 'add_file')

    def _open_add(self, title, dialog, mode):
        dlg = dialog(self, title, style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.panel.update_mp3_listing(dlg.GetPath(), mode)
            dlg.Destroy()

    def on_clear_menu(self, event):
        self.panel.update_mp3_listing(None, 'clear')

    def on_hide(self, event):
        self.panel.list_ctrl.Hide()

    def on_show(self, event):
        self.panel.list_ctrl.Show()

class Mp3Panel(wx.Panel):
    #main body of the mp3 player
    def __init__(self, parent):
        super().__init__(parent)
        super().SetBackgroundColour(wx.WHITE)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #add stop button
        stop_bt = self.create_bitmap_button('stop.png', self.stop_music)
        top_sizer.Add(stop_bt, 0, wx.ALL, 0)
        #add play button
        play_bt = self.create_bitmap_button('play.png', self.start_music)
        top_sizer.Add(play_bt, 0, wx.ALL, 0)
        #add pasue button
        pause_bt = self.create_bitmap_button('pause.png', self.pause_music)
        top_sizer.Add(pause_bt, 0, wx.ALL, 0)
        #add back button
        back_bt = self.create_bitmap_button('rewind.png', self.rewind_music)
        top_sizer.Add(back_bt, 0, wx.ALL, 0)
        #add forward button
        forward_bt = self.create_bitmap_button('forward.png', self.forward_music)
        top_sizer.Add(forward_bt, 0, wx.ALL, 0)
        #add volume slider
        self.current_volume = 50
        self.volume_slider = wx.Slider(self, value=self.current_volume, minValue=0, maxValue=100)
        self.volume_slider.Bind(wx.EVT_SLIDER, self.on_volume_slider)
        top_sizer.Add(self.volume_slider, 0, wx.ALL, 0)
        #add info label
        info_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.ITALIC, wx.NORMAL)
        self.info_label = wx.StaticText(self, label="Choose MP3", size=(200, 36), style=wx.ALIGN_LEFT)
        self.info_label.SetFont(info_font)
        self.info_label.SetBackgroundColour(wx.BLACK)
        self.info_label.SetForegroundColour(wx.GREEN)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_info, self.timer)
        self.timer.Start(100)
        top_sizer.Add(self.info_label, 0, wx.ALL, 0)
        #init info
        self.init_info()
        #add top sizer to main sizer
        main_sizer.Add(top_sizer, 0, wx.ALL, 0)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #add MP3 info
        self.row_obj_dict = {}
        self.mp3s = []
        self.list_ctrl = wx.ListCtrl(self, size=(-1, 200), style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.InsertColumn(0, 'Artist', width=140)
        self.list_ctrl.InsertColumn(1, 'Album', width=140)
        self.list_ctrl.InsertColumn(2, 'Title', width=200)
        bottom_sizer.Add(self.list_ctrl, 0, wx.ALL, 5)
        #add bottom sizer to main sizer
        main_sizer.Add(bottom_sizer, 0, wx.ALL, 0)
        self.SetSizer(main_sizer)
        #init the pygame mixer
        pygame.mixer.init()

    def create_bitmap_button(self, filepath, my_handler):
        bmp = wx.Bitmap(filepath, wx.BITMAP_TYPE_PNG)
        bmp_bt = wx.BitmapButton(
            self, id=wx.ID_ANY, bitmap=bmp,
            size=(bmp.GetWidth()+5, bmp.GetHeight()+5))
        bmp_bt.Bind(wx.EVT_BUTTON, my_handler)
        return bmp_bt

    def on_volume_slider(self, event):
        self.current_volume = self.volume_slider.GetValue() / 100
        pygame.mixer.music.set_volume(self.current_volume)

    def init_info(self):
        self.playing_mp3_tag = '-' * 15 + 'BeBe MP3 Player --- set your music' + '-' * 10
        self.len_tag = len(self.playing_mp3_tag)
        self.slice_1 = 0
        self.slice_2 = 28

    def update_info(self, event):
        self.info_label.SetLabel(f' {self.playing_mp3_tag[self.slice_1:self.slice_2]}')
        self.slice_1 += 1
        self.slice_2 += 1
        if self.slice_1 == self.len_tag:
            self.slice_1 = 0
            self.slice_2 = 28

    def update_mp3_listing(self, folder_path, mode):
        self.list_ctrl.ClearAll()
        self.list_ctrl.InsertColumn(0, 'Artist', width=140)
        self.list_ctrl.InsertColumn(1, 'Album', width=140)
        self.list_ctrl.InsertColumn(2, 'Title', width=200)

        if mode == 'open_folder':
            # self.current_folder_path = folder_path
            self.mp3s = glob.glob(folder_path + '/*.mp3')
        elif mode == 'open_file':
            self.mp3s = [folder_path]
        elif self.mp3s and mode == 'add_folder':
            # self.current_folder_path = folder_path
            new_mp3s = glob.glob(folder_path + '/*.mp3')
            self.mp3s += new_mp3s
        elif self.mp3s and mode == 'add_file':
            print('inn add file')
            self.mp3s.append(folder_path)
        else:
            self.mp3s = []
        mp3_objects = []
        index = 0
        for mp3 in self.mp3s:
            mp3_object = eyed3.load(mp3)
            self.list_ctrl.InsertItem(index, mp3_object.tag.artist)
            self.list_ctrl.SetItem(index, 1, mp3_object.tag.album)
            self.list_ctrl.SetItem(index, 2, mp3_object.tag.title)
            mp3_objects.append(mp3_object)
            self.row_obj_dict[index] = mp3, mp3_object.tag.artist + '-' + mp3_object.tag.album + '-' + mp3_object.tag.title
            index += 1

    def stop_music(self, event):
        self.stop_playing = True
        pygame.mixer.music.stop()

    def start_music(self, event):
        self.stop_playing = False
        self.selection = self.list_ctrl.GetFocusedItem()
        if self.selection >= 0:
            if pygame.mixer.music.get_busy() == 0:
                self.new_thread = threading.Thread(target=self._play_music_thread)
                self.new_thread.start()
            else:
                pygame.mixer.music.unpause()

    def _play_music_thread(self):
        play_list = self.row_obj_dict.keys()
        for _ in range(len(play_list)):
            mp3 = self.row_obj_dict[self.selection][0]
            self.playing_mp3_tag = '-' * 15 + self.row_obj_dict[self.selection][1] + '-' * 10
            pygame.mixer.music.load(mp3)
            pygame.time.Clock()
            try:
                pygame.mixer.music.play()
            except pygame.error:
                break
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(5)
            if self.stop_playing:
                break
            self.selection += 1

    def pause_music(self, event):
        pygame.mixer.music.pause()

    def rewind_music(self, event):
        try:
            if self.selection >= 1:
                self.selection -= 1
                mp3 = self.row_obj_dict[self.selection][0]
                self.playing_mp3_tag = '-' * 15 + self.row_obj_dict[self.selection][1] + '-' * 10
                pygame.mixer.music.load(mp3)
                pygame.mixer.music.play()
        except AttributeError:
            print('Not playing yet')
        except pygame.error:
            print('click play')

    def forward_music(self, event):
        try:
            if self.selection >= 0:
                self.selection += 1
                # try:
                mp3 = self.row_obj_dict[self.selection][0]
                self.playing_mp3_tag = self.row_obj_dict[self.selection][1]
                pygame.mixer.music.load(mp3)
                pygame.mixer.music.play()
        except AttributeError:
            print('Not playing yet')
        except KeyError:
            print('Out of track list')
        except pygame.error:
            print('click play')


if __name__ == '__main__':
    app = wx.App()
    frame = Mp3Frame()
    app.MainLoop()
