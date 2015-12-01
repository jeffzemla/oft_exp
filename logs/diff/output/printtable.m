% matoutput(model,subj).Minimum(cond,param)

% load matoutput

% model 1 all free to vary
% model 2 drift rate and ter vary, boundary fixed
% model 3 empty?
% model 4 empty?

a=[]; % decision boundary
v=[]; % drift rate
ter=[]; % non-decision time

for i=1:26
    a=[a matoutput(1,i).Minimum(:,1)];
    v=[v matoutput(1,i).Minimum(:,7)];
    ter=[ter matoutput(1,i).Minimum(:,2)];
end

a=a';
v=v';
ter=ter';

csvwrite('a.csv',a);
csvwrite('v.csv',v);
csvwrite('ter.csv',ter);
