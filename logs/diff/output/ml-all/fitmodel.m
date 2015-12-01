%addpath('../dmatoolbox/')
files=dir('*.tab')
matoutput=[] % use matouput(:,1) etc.

for logfile = 1:size(files,1)
    data=dlmread(files(logfile).name);
    %data=data(data(:,1)>4,:); % select only mixed block
    %data(data(:,1)==5)=1; % collapse across pre-cue
    %data(data(:,1)==7)=1;
    %data(data(:,1)==6)=2;
    %data(data(:,1)==8)=2;
    options = multiestv4();
    options = repmat(options,1,1);
    
    % reduced parameter model -- needed if i'm going to compare to optimal values derived via analytic solution
    o=[NaN,NaN,0,NaN,0,0,NaN,NaN,NaN]; % no variability in v (eta), zo (sz), and ter (st)

    % matrix {a,ter,eta,zo,sz,st,v,pi?,gamma?}
    % for mixture model: pi=proportion nonoutliers, proportion guesses
    % '1'=column, []=identity
    options(1).DesignMatrix={[],[],[],[],[],[],[],'1','1'};
    options(1).name='everything free to vary';
    options(1).SpecificBias=[.5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5 .5]; % constrain model to have no bias in starting point
    options(1).FixedValues=[o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o;o];
    %options(1).EstimationMethodScalar=2;

    %options(4).name='drift rate varies, boundary and ter fixed';
    %options(4).DesignMatrix={'1','1',[],[],[],[],[],'1','1'};
    %options(4).SpecificBias=[.5 .5 .5 .5]; 
    %options(4).FixedValues=[o;o;o;o];
    %%options(4).EstimationMethodScalar=2;

    %options(3).name='drift rate and boundary vary, ter fixed';
    %options(3).DesignMatrix={[],'1',[],[],[],[],[],'1','1'};
    %options(3).SpecificBias=[.5 .5 .5 .5]; 
    %options(3).FixedValues=[o;o;o;o];
    %%options(3).EstimationMethodScalar=2;

    %options(2).name='drift rate and ter vary, boundary fixed';
    %options(2).DesignMatrix={'1',[],[],[],[],[],[],'1','1'};
    %options(2).SpecificBias=[.5 .5]; 
    %options(2).FixedValues=[o;o];
    %options(2).EstimationMethodScalar=2;
    
    output=multiestv4(data,options);  
    matoutput=[matoutput output]
    qtable(output)
    output.Minimum
end

save matoutput
