import random, time, ffmpeg
import numpy as np


# Reads train/test filenames from provided splits
# Returns video directions and their labels in a list
def get_data_dir(filename):
    dir_videos, label_videos = [], []
    with open(filename, 'r') as input_file:
        for line in input_file:
            file_name, label = line.split(' ')
            dir_videos.append(file_name)
            label_videos.append(int(label))
    return dir_videos, label_videos


# Shuffles video directions along with labels
def shuffle_list(dir_videos, label_videos, seed=time.time()):
    video_indices = list(range(len(dir_videos)))
    random.seed(seed)
    random.shuffle(video_indices)
    shuffled_video_dirs = [dir_videos[i] for i in video_indices]
    shuffled_labels = [label_videos[i] for i in video_indices]
    return shuffled_video_dirs, shuffled_labels


# Given video directory it reads the video
# extracts the frames, and do preprocessing operation
def read_clip(dirname, model_settings):
    frames_per_batch = model_settings['frames_per_batch']
    video_fps = model_settings['video_fps']
    crop_size = model_settings['crop_size']
    np_mean = model_settings['np_mean']
    horizontal_flip = random.random()

    probe = ffmpeg.probe(dirname)
    video_info = probe["streams"][0]
    video_width = video_info["width"]
    video_height = video_info["height"]
    video_duration = float(video_info["duration"])
    num_frame = int(video_info["nb_frames"])

    rand_max = int(num_frame - ((num_frame / video_duration) * (frames_per_batch / video_fps)))
    start_frame = random.randint(0, rand_max - 1)
    #end_frame = ceil(start_frame + (num_frame / video_duration) * frames_per_batch / video_fps + 1)
    video_start = (video_duration / num_frame) * start_frame
    video_end = video_start + ((frames_per_batch+1) / video_fps)

    x_pos = max(video_width - video_height, 0) // 2
    y_pos = max(video_height - video_width, 0) // 2
    crop_size1 = min(video_height, video_width)
    # Read specified times of the video
    ff = ffmpeg.input(dirname, ss=video_start, t=video_end-video_start)
    # Trim video -> did not work :(
    # ff = ff.trim(end_frame='50')
    # Divide into frames
    ff = ffmpeg.filter(ff, 'fps', video_fps)
    # Crop
    ff = ffmpeg.crop(ff, x_pos, y_pos, crop_size1, crop_size1)
    # Subsample
    ff = ffmpeg.filter(ff, 'scale', crop_size, crop_size)
    # Horizontal flip with some probability
    if horizontal_flip > 0.5:
        ff = ffmpeg.hflip(ff)
    # Output the video
    ff = ffmpeg.output(ff, 'pipe:',
                       format='rawvideo',
                       pix_fmt='rgb24')
    # Run Process in quiet mode
    out, _ = ffmpeg.run(ff, capture_stdout=True, quiet=True)
    # Extract to numpy array
    video = np.frombuffer(out, np.uint8). \
        reshape([-1, crop_size, crop_size, 3])

    # Subtracts the mean and converts type to float32
    video = video[:16] - np_mean
    return video


# TODO: Check reading with thread and time it consumes
# time0 = time.time()
# for read_index in range(10):
#    video_dir, label = dir_videos[read_index], label_clips[read_index]
#    video_dir = model_settings['data_home'] + video_dir
#    video = read_clip(video_dir, model_settings)
# print('Time diff:', time.time() - time0)