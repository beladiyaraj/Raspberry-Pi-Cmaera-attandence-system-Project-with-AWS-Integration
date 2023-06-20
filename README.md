<h1 style="font-size: 32px;"><b>Raspberry Pi Webcam Project with AWS Integration</b></h1>

<p><i>Capture, Store, and Analyze Photos with Ease! 📸🔒🔍</i></p>

<p>This repository contains the code and documentation for a <b style="font-size: 24px;">Raspberry Pi webcam project</b> with <b style="font-size: 24px;">AWS integration</b>. The project utilizes a USB webcam (specifically the <i>Mi USB Webcam HD</i>) connected to a Raspberry Pi to capture photos and seamlessly upload them to an Amazon S3 bucket for storage and further processing. It leverages the power of AWS services to enhance the functionality and scalability of the project.</p>

<h2 style="font-size: 28px;"><b>Features:</b></h2>
<ol>
  <li>Capture photos from multiple USB webcams connected to the Raspberry Pi</li>
  <li>Adjustable camera settings such as <i>brightness</i>, <i>contrast</i>, <i>gamma</i>, <i>sharpness</i>, and <i>saturation</i></li>
  <li>Automatic upload of captured photos to an Amazon S3 bucket for secure storage and easy access</li>
  <li>Integration with AWS SDK (Boto3) for seamless interaction with S3 services</li>
  <li>Batch numbering system to organize and manage captured photos effectively</li>
  <li>GPIO button integration for manual photo capture</li>
  <li>Detailed logging for error tracking and debugging purposes</li>
</ol>

<h2 style="font-size: 28px;"><b>Requirements:</b></h2>
<ul>
  <li>Raspberry Pi (tested on Raspberry Pi 4 Model B)</li>
  <li>USB webcams (compatible with V4L2)</li>
  <li>Python 3</li>
  <li>RPi.GPIO library</li>
  <li>fswebcam package for capturing photos</li>
  <li>Boto3 library for AWS SDK integration</li>
  <li>An AWS account with necessary permissions to access S3, Lambda, and Comprehend services</li>
</ul>

<h2 style="font-size: 28px;"><b>AWS Services Used:</b></h2>
<ul>
  <li><b style="font-size: 20px;">Amazon S3:</b> Securely store and manage the captured photos in a scalable cloud storage solution</li>
  <li>AWS SDK (Boto3): Interact with AWS services programmatically to upload photos to S3</li>
  <li><b style="font-size: 20px;">AWS Lambda:</b> Execute serverless functions to process the captured photos, perform image analysis, or generate custom notifications</li>
  <li><b style="font-size: 20px;">AWS Comprehend:</b> Utilize natural language processing (NLP) capabilities to extract insights and perform sentiment analysis from textual data associated with the captured photos</li>
</ul>

<h2 style="font-size: 28px;"><b>AWS Flavor:</b></h2>
<p>This project incorporates AWS services to provide a scalable and reliable solution for storing and managing photos captured by the Raspberry Pi webcam. By leveraging <b style="font-size: 20px;">Amazon S3</b>, the project ensures secure and durable storage of the photos, making them easily accessible from anywhere. The AWS SDK integration allows seamless interaction with S3 services, enabling automated uploads and efficient management of the photo collection. <b style="font-size: 20px;">AWS Lambda</b> provides the ability to execute serverless functions, which can be utilized for image analysis tasks, custom notifications, or any other processing needs. Additionally, <b style="font-size: 20px;">AWS Comprehend</b> can be used to extract insights and perform sentiment analysis on any textual data associated with the captured photos, enabling deeper analysis and understanding.</p>

<h2 style="font-size: 28px;"><b>Requirements:</b></h2>
<ul>
  <li>Raspberry Pi (tested on Raspberry Pi 4 Model B)</li>
  <li>USB webcams (compatible with V4L2)</li>
  <li>Python 3</li>
  <li>RPi.GPIO library</li>
  <li>fswebcam package for capturing photos</li>
  <li>Boto3 library for AWS SDK integration</li>
  <li>An AWS account with necessary permissions to access S3, Lambda, and Comprehend services</li>
</ul>

<h2 style="font-size: 28px;"><b>Get Started Today!</b></h2>
<p>Contribution, issue reporting, and suggestions for improvement are <b style="font-size: 24px;">highly appreciated</b>.</p>
