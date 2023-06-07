#!/usr/bin/env perl 

use strict; 
use warnings; 

    my $name = '\\.+test.+\\'; 
	my $counter = 0;
	my $LINEOUT = '';

    open( FILE, "<cloc.xml" ); 
    my @LINES = <FILE>; 
    close( FILE ); 
    open( FILE, ">cloc.xml" ); 
    foreach my $LINE ( @LINES ) { 
#	if ( $LINE =~ m/
        print FILE $LINE unless (( $LINE =~ m/bypassing/ ) ||( $LINE =~ m/\\traptest/ ) ||( $LINE =~ m/\\test_/ ) ||( $LINE =~ m/unittest/ ) ||( $LINE =~ m/_test/ ) || ( $LINE =~ m/_cppunit/ ) ||( $LINE =~ m/cpp11_gtest/ ) ||( $LINE =~ m/testutil/ ) || ( $LINE =~ m/\\_test\\/ ) || ( $LINE =~ m/\\gtest\\/ ) || ( $LINE =~ m/\\gtest-1.8\\/ ) || ( $LINE =~ m/\\test\\/ ) || ( $LINE =~ m/\\Test/ ) || ( $LINE =~ m/Test\\/ ) || ( $LINE =~ m/\\unittest\\/ ) || ( $LINE =~ m/\\tests\\/ ) || ( $LINE =~ m/\\_Tests\\/ ) || ( $LINE =~ m/testing/ )  ); 
    } 
    close( FILE ); 
	open( FILE, "<cloc.xml" ); 
	my $name1 = 'file name';
	my $name2 = '<n_files>.+<\/n_files>';
	my $name3 = '<report_file>.+<\/report_file>';
    my @LINES1 = <FILE>; 
	foreach my $LINE ( @LINES1 ) {
		if ($LINE =~ m/$name1/ ){
			$counter = $counter + 1;
		}
	}
    close( FILE );
	open( FILE, ">cloc.xml" ); 
	foreach my $LINE ( @LINES1 ) {
		if ($LINE =~ m/$name2/ ){
			$LINE =~ s/<n_files>.+<\/n_files>/<n_files>$counter<\/n_files>/ig;
			print FILE $LINE;
		}
		else {
			if ($LINE =~ m/$name3/ ){
				$LINE =~ s/<report_file>.+<\/report_file>/<report_file>cloc.xml<\/report_file>/ig;
				print FILE $LINE;
			}
			else {
				print FILE $LINE;
			}
		}
	}
    close( FILE );
    print( "<n_files>$counter<\/n_files>" ); 
	
	
		