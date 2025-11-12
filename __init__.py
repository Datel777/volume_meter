bl_info = {
    "name": "Display Volume Meter",
    "author": "SNU, tintwotin",
    "version": (1, 0),
    "blender": (3, 40, 0),
    "location": "Timeline > Header",
    "description": "Displays the current volume of the VSE sequence at the current frame in Timeline header",
    "category": "Sequencer"
}

import bpy
# source: https://github.com/snuq/VSEQF/
# The main functions are made by SNU for his VSEQF, this is just a simple implementation of a volume meter which shows up in the Timeline editor.

def get_fade_curve(context, sequence):
    #Returns the fade curve for a given sequence.  If create is True, a curve will always be returned, if False, None will be returned if no curve is found.

    #Search through all curves and find the fade curve
    animation_data = context.scene.animation_data
    if not animation_data:
        return None

    action = animation_data.action
    if not action:
        return None

    all_curves = action.fcurves
    fade_curve = None  #curve for the fades
    for curve in all_curves:
        if curve.data_path == 'sequence_editor.sequences_all["'+sequence.name+'"].volume':
            #keyframes found
            return curve

    return None


def get_sequence_volume(frame=None):
    if bpy.context.scene.sequence_editor is None:
        return 0
    
    sequences = bpy.context.scene.sequence_editor.sequences_all
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    if frame is None:
        frame = bpy.context.scene.frame_current
        evaluate_volume = False
    else:
        evaluate_volume = True

    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    total = 0

    for sequence in sequences:
        if sequence.mute:
            continue

        if sequence.type == "SOUND" and sequence.frame_final_start < frame < sequence.frame_final_end:
            time_from = (frame - 1 - sequence.frame_start) / fps
            time_to = (frame - sequence.frame_start) / fps

            audio = sequence.sound.evaluated_get(depsgraph).factory

            chunk = audio.limit(time_from, time_to).data()
            #sometimes the chunks cannot be read properly, try to read 2 frames instead
            if len(chunk)==0:
                time_from_temp = (frame - 2 - sequence.frame_start) / fps
                chunk = audio.limit(time_from_temp, time_to).data()
			
            #chunk still couldnt be read... just give up :\
            if len(chunk) != 0:
                cmax = abs(chunk.max())
                cmin = abs(chunk.min())
                if cmax > cmin:
                    average = cmax
                else:
                    average = cmin

                if evaluate_volume:
                    fcurve = get_fade_curve(bpy.context, sequence)
                    if fcurve:
                        total += fcurve.evaluate(frame) * average
                    else:
                        total += sequence.volume * average
                else:
                    total += sequence.volume * average

    return round(total, 4)



def update_volume(self, context):

    scene = context.scene
    if scene.old_frame != scene.frame_current:
        scene.volume = get_sequence_volume(scene.frame_current)
        scene.old_frame = scene.frame_current


def draw_volume_slider(self, context):
    layout = self.layout
    scene = context.scene
    if scene.volume > 1:
        vu_icon = "OUTLINER_OB_SPEAKER"
    else: 
        vu_icon = "OUTLINER_DATA_SPEAKER"
    layout.separator()
    layout = layout.box()
    layout.scale_y = 1.2
    layout.scale_x = 1.2
    row = layout.row(align=True)
    # row.enabled = False
    row.label(text="", icon= vu_icon)
    row.scale_y = .8
    row.prop(scene, "volume", text="                          ", slider=True, icon = vu_icon)


def register():
    bpy.types.Scene.old_frame = bpy.props.IntProperty( name="Old Frame", default=0, min=0, max=100000000)
    bpy.types.Scene.volume = bpy.props.FloatProperty(
        name="Volume", default=0.0, min=-0.0, max=2.0, precision = 4)
    bpy.types.TIME_MT_editor_menus.append(draw_volume_slider)
    bpy.app.handlers.frame_change_post.append(update_volume)


def unregister():
    bpy.types.TIME_MT_editor_menus.remove(draw_volume_slider)
    bpy.app.handlers.frame_change_post.remove(update_volume)
    del bpy.types.Scene.volume
    del bpy.types.Scene.old_frame


if __name__ == "__main__":
    register()
