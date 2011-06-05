# this sed script parses some data from a HTTP header

# parse HTTP code and consume the line
s/^\s*HTTP\S*\s*\([0-9]\{3\}\) \(.*\)\r$/CODE='\1';STATUSMSG='\2'/;t
# parse some HTTP header fields and comsume the line
s/^\s*content-type\s*:\s*\(.*\).$/CONTENT_TYPE='\1'/i;t
s/^\s*etag\s*:\s*\(.*\).$/ETAG='\1'/i;t
s/^\s*location\s*:\s*\(.*\).$/LOCATION='\1'/i;t
s/^\s*x-up-to-date\s*:\s*\(.*\).$/X_UP_TO_DATE='\1'/i;t

# DEBUG: comment any line not recognized above
## s/^\(.*\)$/# \1/;t

# consume all other lines, but do not display them
d
