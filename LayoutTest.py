import time
from WordChain import *
from Layout import MessageVisualizer

print(time.asctime())

wc = WordChain()
wc.depth = 3
print(time.asctime(), "Reading map")
wc.read_map("Composite.txt.map")
last_message = ''
mv = MessageVisualizer(wc)

a = input("Prompt: ")
print(time.asctime(), "Building messages")

while len(a) == 0 or a[0] not in ('q', 'Q'):
    for i in range(1):
        attempts = 1
        sources = []
        if len(a) == 0:
            mpath = wc.build_message_path(char_limit=140, word_count=200, prompt=a, sources=sources)
            message = wc.render_message_from_path(mpath)
            while message[0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' or message[-1] not in '.!?' or len(message) < 30:
                sources = []
                mpath = wc.build_message_path(char_limit=140, word_count=200, prompt=a, sources=sources)
                message = wc.render_message_from_path(mpath)
                attempts += 1
                if attempts > 10:
                    a = ""
        else:
            message = a
            mpath = wc.find_path_for_message(message)
            sources = []
            for set_node in mpath:
                wc.append_node_sources(set_node, sources)

    mv.build_graph_display(mpath)
    previous_prompt = a
    a = input("Prompt:")
    if len(a) > 5 and a[:5] == 'size:':
        mv.node_size = int(a[5:])
        a = previous_prompt
    elif len(a) > 6 and a[:6] == 'depth:':
        mv.depth = int(a[6:])
        a = previous_prompt
    elif len(a) > 7 and a[:7] == 'weight:':
        mv.base_edge_weight = int(a[7:])
        a = previous_prompt
    elif len(a) > 4 and a[:4] == 'ewm:':
        mv.edge_weight_multiplier = float(a[4:])
        a = previous_prompt
    elif len(a) > 5 and a[:5] == 'cmap:':
        MessageVisualizer.gradient_color_map = a[5:]
        a = previous_prompt
    elif len(a) > 6 and a[:6] == 'scale:':
        mv.scale = int(a[6:])
        a = previous_prompt



# color values: Accent, Accent_r, Blues, Blues_r, BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, CMRmap, CMRmap_r,
        # Dark2, Dark2_r, GnBu, GnBu_r, Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, Oranges, Oranges_r,
        # PRGn, PRGn_r, Paired, Paired_r, Pastel1, Pastel1_r, Pastel2, Pastel2_r, PiYG, PiYG_r, PuBu, PuBuGn,
        # PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, Purples, Purples_r, RdBu, RdBu_r, RdGy, RdGy_r, RdPu,
        # RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, RdYlGn_r, Reds, Reds_r, Set1, Set1_r, Set2, Set2_r, Set3, Set3_r,
        # Spectral, Spectral_r, Vega10, Vega10_r, Vega20, Vega20_r, Vega20b, Vega20b_r, Vega20c, Vega20c_r,
        # Wistia, Wistia_r, YlGn, YlGnBu, YlGnBu_r, YlGn_r, YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, afmhot_r,
        # autumn, autumn_r, binary, binary_r, bone, bone_r, brg, brg_r, bwr, bwr_r, cool, cool_r,
        # coolwarm, coolwarm_r, copper, copper_r, cubehelix, cubehelix_r, flag, flag_r, gist_earth,
        # gist_earth_r, gist_gray, gist_gray_r, gist_heat, gist_heat_r, gist_ncar, gist_ncar_r, gist_rainbow,
        # gist_rainbow_r, gist_stern, gist_stern_r, gist_yarg, gist_yarg_r, gnuplot, gnuplot2, gnuplot2_r,
        # gnuplot_r, gray, gray_r, hot, hot_r, hsv, hsv_r, inferno, inferno_r, jet, jet_r, magma, magma_r,
        # nipy_spectral, nipy_spectral_r, ocean, ocean_r, pink, pink_r, plasma, plasma_r, prism, prism_r,
        # rainbow, rainbow_r, seismic, seismic_r, spectral, spectral_r, spring, spring_r, summer, summer_r,
        # terrain, terrain_r, viridis, viridis_r, winter, winter_r