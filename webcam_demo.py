import tensorflow as tf
import cv2
import time
import argparse
import csv

import posenet

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=int, default=101)
parser.add_argument('--cam_id', type=int, default=0)
parser.add_argument('--cam_width', type=int, default=1280)
parser.add_argument('--cam_height', type=int, default=720)
parser.add_argument('--scale_factor', type=float, default=0.7125)
parser.add_argument('--file', type=str, default="online_walk.mp4", help="Optionally use a video file instead of a live camera")
args = parser.parse_args()


def main():
    with tf.Session() as sess:
        model_cfg, model_outputs = posenet.load_model(args.model, sess)
        output_stride = model_cfg['output_stride']

        if args.file is not None:
            cap = cv2.VideoCapture(args.file)
        else:
            cap = cv2.VideoCapture(args.cam_id)
        cap.set(3, args.cam_width)
        cap.set(4, args.cam_height)

        start = time.time()
        frame_count = 0

        # header = ['action','frame', 'input_number', 'x_inputs', 'y_inputs']
        #
        # with open('dataset.csv','w') as w:
        #     do = csv.writer(w)
        #     do.writerow(header)

        while True:
            input_image, display_image, output_scale = posenet.read_cap(
                cap, scale_factor=args.scale_factor, output_stride=output_stride)

            heatmaps_result, offsets_result, displacement_fwd_result, displacement_bwd_result = sess.run(
                model_outputs,
                feed_dict={'image:0': input_image}
            )

            pose_scores, keypoint_scores, keypoint_coords = posenet.decode_multi.decode_multiple_poses(
                heatmaps_result.squeeze(axis=0),
                offsets_result.squeeze(axis=0),
                displacement_fwd_result.squeeze(axis=0),
                displacement_bwd_result.squeeze(axis=0),
                output_stride=output_stride,
                max_pose_detections=10,
                min_pose_score=0.15)

            keypoint_coords *= output_scale

            frame = []
            action_name = []
            position = []
            x_coordinates = []
            y_coordinates = []
            for i, j in enumerate(keypoint_coords[0]):
                action_name.append('walking')
                frame.append(frame_count)
                position.append(i + 1)
                x_coordinates.append(j[0])
                y_coordinates.append(j[1])
            print(f'Frame is {frame}, body pos {position}, x value {x_coordinates}, y value {y_coordinates}')

            # TODO this isn't particularly fast, use GL for drawing and display someday...
            overlay_image = posenet.draw_skel_and_kp(
                display_image, pose_scores, keypoint_scores, keypoint_coords,
                min_pose_score=0.15, min_part_score=0.1)
            #print(cap.get(cv2.CAP_PROP_FPS))
            #print(len(keypoint_scores[0]))

            print(keypoint_coords[0])

            cv2.imshow('posenet', overlay_image)
            frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            print('Average FPS: ', frame_count / (time.time() - start))

            rows = zip(action_name,frame,position,x_coordinates,y_coordinates)

            with open('dataset.csv','a') as f:
                writer = csv.writer(f)
                #writer.writerow(header)
                for row in rows:
                    writer.writerow(row)



if __name__ == "__main__":
    main()