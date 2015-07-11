# -*- coding: utf-8 -*-

def convert_index(indices):
    padded_indices = []
    for index in indices:
        parts = index.split('-')
        track_index = "-%02d" % (int(parts.pop()),)
        padded_indices.append('%s%s' % (''.join(parts), track_index))

    return sorted(padded_indices)

if __name__ == '__main__':
    indices = ['1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8', '1-9', '1-10', '1-11', '1-20', '1-21', '2-1', '2-2', '2-3', '2-4', '2-5', '2-6', '2-7', '2-8', '2-9', '2-10', '2-11', '2-20', '2-21']
    print convert_index(indices)